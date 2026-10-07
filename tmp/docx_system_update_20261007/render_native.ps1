param(
  [string]$InputDocx = 'C:\Users\Insun\semi-auto-researching-corporate\output\documents\corporate_research_system_update_20261007.docx',
  [string]$RenderDirectory = 'C:\Users\Insun\semi-auto-researching-corporate\tmp\docx_system_update_20261007\render'
)
$ErrorActionPreference = 'Stop'
$null = New-Item -ItemType Directory -Path $RenderDirectory -Force
$pdfPath = Join-Path $RenderDirectory 'document.pdf'
$word = $null
$document = $null
try {
  Write-Output 'Starting hidden Word'
  $word = New-Object -ComObject Word.Application
  Write-Output 'Word initialized'
  $word.Visible = $false
  $word.DisplayAlerts = 0
  Write-Output 'Opening DOCX read only'
  $document = $word.Documents.Open($InputDocx, $false, $true)
  Write-Output 'DOCX opened'
  $null = $document.Fields.Update()
  $document.Repaginate()
  $pageCount = $document.ComputeStatistics(2)
  $layout = @()
  foreach ($p in $document.Paragraphs) {
    $text = $p.Range.Text.Trim()
    if ($text.Length -gt 0 -and $p.OutlineLevel -le 2) {
      $layout += [pscustomobject]@{Heading=$text; Page=$p.Range.Information(3)}
    }
  }
  $layout | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $RenderDirectory 'heading_pages.json') -Encoding UTF8
  Write-Output "Exporting $pageCount pages"
  $word.Options.PrintBackground = $false
  $document.ExportAsFixedFormat($pdfPath, 17, $false, 0, 0, 1, 1, 0, $false, $false, 0, $true, $true, $false)
  Write-Output 'PDF exported'
  [pscustomobject]@{Pages=$pageCount; Pdf=$pdfPath} | ConvertTo-Json -Compress
} finally {
  if ($null -ne $document) { $document.Close(0); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) }
  if ($null -ne $word) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) }
}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType=WindowsRuntime]
$genericAsTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
$actionAsTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1
function Wait-Operation($operation, [Type]$resultType) {
  $task = $genericAsTask.MakeGenericMethod($resultType).Invoke($null, @($operation))
  $task.GetAwaiter().GetResult()
}
function Wait-Action($operation) {
  $task = $actionAsTask.Invoke($null, @($operation))
  $task.GetAwaiter().GetResult()
}
$file = Wait-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfPath)) ([Windows.Storage.StorageFile])
$pdf = Wait-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
for ($i = 0; $i -lt $pdf.PageCount; $i++) {
  $pdfPage = $pdf.GetPage($i)
  $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
  $options = New-Object Windows.Data.Pdf.PdfPageRenderOptions
  $options.DestinationWidth = 1500
  Wait-Action ($pdfPage.RenderToStreamAsync($stream, $options))
  $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
  $null = Wait-Operation ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
  $bytes = New-Object byte[] ([int]$stream.Size)
  $reader.ReadBytes($bytes)
  [System.IO.File]::WriteAllBytes((Join-Path $RenderDirectory ('page-{0}.png' -f ($i + 1))), $bytes)
  $reader.Dispose(); $stream.Dispose(); $pdfPage.Dispose()
}
[pscustomobject]@{RenderedPages=$pdf.PageCount; Renderer='Microsoft Word PDF and Windows PDF page renderer'; Directory=$RenderDirectory} | ConvertTo-Json -Compress
