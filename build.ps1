param(
    [string]$msg = ""
)

Set-Location "C:\JARVIS2"

# --- VERIFICACION ---
if (-not (Test-Path "C:\JARVIS2\jarvis.ps1")) {
    Write-Host "ERROR: no se encuentra jarvis.ps1 en C:\JARVIS2" -ForegroundColor Red
    exit 1
}

# --- COMPILACION ---
Write-Host "[Build] Compilando jarvis.exe..." -ForegroundColor Cyan
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Import-Module ps2exe -ErrorAction Stop
Invoke-ps2exe "C:\JARVIS2\jarvis.ps1" "C:\JARVIS2\jarvis.exe" -noConsole:$false

if (-not (Test-Path "C:\JARVIS2\jarvis.exe")) {
    Write-Host "ERROR: compilacion fallida." -ForegroundColor Red
    exit 1
}
Write-Host "    OK -- jarvis.exe generado" -ForegroundColor Green

# --- COMMIT ---
$isRepo = git rev-parse --is-inside-work-tree 2>$null
if (-not $isRepo) {
    Write-Host "AVISO: no es un repositorio git. Compilacion completada sin commit." -ForegroundColor Yellow
    exit 0
}

if ($msg -eq "") {
    $msg = Read-Host "Mensaje de commit"
}

if ($msg -eq "") {
    Write-Host "AVISO: mensaje vacio. Compilacion completada sin commit." -ForegroundColor Yellow
    exit 0
}

git add jarvis.ps1 jarvis.exe launcher.py setup.ps1 system.md config.yaml
git commit -m $msg
Write-Host "    OK -- commit realizado: $msg" -ForegroundColor Green
