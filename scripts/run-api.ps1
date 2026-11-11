param([switch]$Reload)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Run python -m venv .venv and install services/api/requirements.txt first.' }
$env:PYTHONPATH = Join-Path $projectRoot 'services\api'
$apiArgs = @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--no-access-log')
if ($Reload) { $apiArgs += '--reload' }
& $pythonPath @apiArgs
