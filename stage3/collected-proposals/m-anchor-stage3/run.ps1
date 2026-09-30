$ErrorActionPreference = 'Stop'
$taskRuntime = Join-Path $PSScriptRoot '..\..\work\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskRuntime)) {
    $taskRuntime = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $taskRuntime)) {
    $taskRuntime = 'python'
}
if ($args.Count -eq 0) {
    $taskResult = Join-Path $PSScriptRoot ('results\replay-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    & $taskRuntime -X utf8 (Join-Path $PSScriptRoot 'replay.py') evaluate --out $taskResult
} else {
    & $taskRuntime -X utf8 (Join-Path $PSScriptRoot 'replay.py') @args
}
exit $LASTEXITCODE
