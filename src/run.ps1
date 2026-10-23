param([switch]$Rebuild, [switch]$White)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $runtimePython) {
    $pythonExe = $runtimePython
} else {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}
$composeScript = Join-Path $PSScriptRoot 'compose.py'
if ($White) {
    & $pythonExe (Join-Path $PSScriptRoot 'build_white_wordmark.py')
} elseif ($Rebuild) {
    & $pythonExe $composeScript --rebuild
} else {
    & $pythonExe $composeScript
}
if ($LASTEXITCODE -ne 0) { throw 'Logo generation failed.' }
