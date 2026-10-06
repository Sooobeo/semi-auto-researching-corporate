$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$env:PYTHONIOENCODING = 'utf-8'
python web/p05/server.py
