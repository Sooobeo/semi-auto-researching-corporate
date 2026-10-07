param(
 [string]$InputDocx='C:\Users\Insun\semi-auto-researching-corporate\output\documents\corporate_research_system_update_20261007.docx',
 [string]$RenderDirectory='C:\Users\Insun\semi-auto-researching-corporate\tmp\docx_system_update_20261007\render_emf'
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$null=New-Item -ItemType Directory -Path $RenderDirectory -Force
$word=$null; $document=$null
try {
 Write-Output 'Starting Word page rendering'
 $word=New-Object -ComObject Word.Application
 $word.Visible=$false; $word.DisplayAlerts=0
 $document=$word.Documents.Open($InputDocx,$false,$true)
 $document.ActiveWindow.View.Type=3
 $document.Repaginate()
 $count=$document.ComputeStatistics(2)
 Write-Output "Pages $count"
 $pages=$document.ActiveWindow.Panes.Item(1).Pages
 for ($i=1; $i -le $count; $i++) {
  $p=$pages.Item($i)
  [byte[]]$bits=$p.EnhMetaFileBits
  $stream=New-Object System.IO.MemoryStream(,$bits)
  $mf=New-Object System.Drawing.Imaging.Metafile($stream)
  $bmp=New-Object System.Drawing.Bitmap(1500,2121)
  $g=[System.Drawing.Graphics]::FromImage($bmp)
  $g.Clear([System.Drawing.Color]::White)
  $g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.DrawImage($mf,[System.Drawing.Rectangle]::new(0,0,1500,2121))
  $bmp.Save((Join-Path $RenderDirectory "page-$i.png"),[System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose(); $mf.Dispose(); $stream.Dispose()
  Write-Output "Rendered $i"
 }
 [pscustomobject]@{Pages=$count;Renderer='Microsoft Word native page metafile';Directory=$RenderDirectory} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $RenderDirectory 'render_manifest.json') -Encoding UTF8
} finally {
 if ($null -ne $document) { $document.Close(0); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) }
 if ($null -ne $word) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) }
}
