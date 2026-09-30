$ErrorActionPreference = 'Stop'

$appPath = Join-Path $PSScriptRoot 'app.py'
$workspacePath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$projectPythonPath = Join-Path $workspacePath 'work/.venv/Scripts/python.exe'
$portablePythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'

if (Test-Path -LiteralPath $projectPythonPath -PathType Leaf) {
    $pythonPath = $projectPythonPath
} elseif (Test-Path -LiteralPath $portablePythonPath -PathType Leaf) {
    $pythonPath = $portablePythonPath
} else {
    Write-Error 'Python environment not found. In this folder, run: py -3 -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt. See README.md.'
    exit 1
}

if (-not (Test-Path -LiteralPath $appPath -PathType Leaf)) {
    Write-Error 'app.py was not found beside run.ps1. Keep the application files together.'
    exit 1
}

& $pythonPath -X utf8 $appPath @args
exit $LASTEXITCODE
