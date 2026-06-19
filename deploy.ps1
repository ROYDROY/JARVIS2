<#
.SYNOPSIS
    JARVIS 4.0 - Pipeline de despliegue unificado
    Secuencia: git pull -> build -> backup
.USAGE
    .\deploy.ps1              # interactivo
    .\deploy.ps1 -Silencioso  # sin prompts, backup a ruta por defecto
#>
param(
    [switch]$Silencioso
)

$ErrorActionPreference = "Stop"
$PROD = "C:\JARVIS2"

Set-Location $PROD

Write-Host "===== JARVIS 4.0 DEPLOY =====" -ForegroundColor Cyan

# --- 1. PULL ---
Write-Host "[1/3] git pull..." -ForegroundColor Gray
$pullResult = git pull 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en git pull: $pullResult" -ForegroundColor Red
    exit 1
}
Write-Host "  OK -- $($pullResult | Select-Object -Last 1)" -ForegroundColor Green

# --- 2. BUILD ---
Write-Host "[2/3] Build..." -ForegroundColor Gray
& "$PROD\build.ps1" -ErrorAction Stop
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en build.ps1" -ForegroundColor Red
    exit 1
}
Write-Host "  OK -- jarvis.exe compilado" -ForegroundColor Green

# --- 3. BACKUP ---
Write-Host "[3/3] Backup..." -ForegroundColor Gray
if ($Silencioso) {
    & "$PROD\backup.ps1" -Silencioso -ErrorAction Stop
} else {
    & "$PROD\backup.ps1" -ErrorAction Stop
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en backup.ps1" -ForegroundColor Red
    exit 1
}
Write-Host "  OK -- backup generado" -ForegroundColor Green

Write-Host "===== DEPLOY COMPLETADO =====" -ForegroundColor Cyan
