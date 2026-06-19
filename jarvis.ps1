# jarvis.ps1 - Lanzador nativo de JARVIS 4.0 compilable a ejecutable exe
$scriptParent = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptParent) { $scriptParent = $PSScriptRoot }
if (-not $scriptParent) { $scriptParent = Get-Location }
Set-Location $scriptParent
if (Test-Path "venv\Scripts\python.exe") {
    & venv\Scripts\python.exe jarvis_app.py
} else {
    & C:\JARVIS2\venv\Scripts\python.exe jarvis_app.py
}
