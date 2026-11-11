$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath (Join-Path $projectRoot 'apps\web')
node --env-file-if-exists=../../.env node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3000
