# setup.ps1 — JARVIS2
# Uso: git clone <repo> && cd <repo> && .\setup.ps1
# Levanta el sistema completo en máquina limpia sin pasos manuales.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Check-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Host "`n=== JARVIS2 SETUP ===" -ForegroundColor Cyan

# ——————————————————————————
# 1. PRECONDICIONES
# ——————————————————————————
Write-Host "`n[1/7] Verificando precondiciones..." -ForegroundColor Yellow

# PowerShell 7+
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "Se requiere PowerShell 7 o superior. Versión detectada: $($PSVersionTable.PSVersion)"
}

# Python 3.10+
if (-not (Check-Command python)) { Write-Error "Python no encontrado en el PATH." }
$pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersion -lt [version]"3.10") { Write-Error "Se requiere Python 3.10+. Detectado: $pyVersion" }

# Git
if (-not (Check-Command git)) { Write-Error "Git no encontrado en el PATH." }

# Espacio en disco (12 GB mínimo)
$drive = Split-Path -Qualifier $root
$freeGB = [math]::Round((Get-PSDrive ($drive.TrimEnd(':'))).Free / 1GB, 1)
if ($freeGB -lt 12) { Write-Error "Espacio insuficiente en disco. Disponible: ${freeGB} GB. Mínimo: 12 GB." }

Write-Host "    OK — PS $($PSVersionTable.PSVersion), Python $pyVersion, Git OK, Disco libre: ${freeGB} GB" -ForegroundColor Green

# ——————————————————————————
# 2. ESTRUCTURA DE CARPETAS
# ——————————————————————————
Write-Host "`n[2/7] Verificando estructura de carpetas..." -ForegroundColor Yellow

$folders = @("logs", "memoria", "sandbox", "skills", "config")
foreach ($f in $folders) {
    $path = Join-Path $root $f
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Host "    Creado: $f" -ForegroundColor Gray
    }
}
Write-Host "    OK" -ForegroundColor Green

# ——————————————————————————
# 3. OLLAMA
# ——————————————————————————
Write-Host "`n[3/7] Verificando Ollama..." -ForegroundColor Yellow

if (-not (Check-Command ollama)) {
    Write-Host "    Ollama no encontrado. Instalando via winget..." -ForegroundColor Gray
    winget install Ollama.Ollama --silent
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    if (-not (Check-Command ollama)) { Write-Error "Instalación de Ollama fallida. Instálalo manualmente desde https://ollama.com" }
}
Write-Host "    OK — $(ollama --version)" -ForegroundColor Green

# ——————————————————————————
# 4. MODELO
# ——————————————————————————
Write-Host "`n[4/7] Verificando modelo..." -ForegroundColor Yellow

$modelList = ollama list 2>&1

$modelos = @(
    [PSCustomObject]@{ Nombre = "qwen2.5:7b-instruct-q5_K_M"; Tamanio = "5.4GB"; Descripcion = "Recomendado — equilibrado" },
    [PSCustomObject]@{ Nombre = "qwen2.5:3b-instruct";        Tamanio = "2.1GB"; Descripcion = "Ligero, menos capaz" },
    [PSCustomObject]@{ Nombre = "llama3.2:3b";                Tamanio = "2.0GB"; Descripcion = "Alternativa ligera" },
    [PSCustomObject]@{ Nombre = "MANUAL";                     Tamanio = "—";     Descripcion = "Introducir nombre manualmente" }
)

$modeloInstalado = $null
foreach ($m in $modelos | Where-Object { $_.Nombre -ne "MANUAL" }) {
    if ($modelList -match $m.Nombre) {
        $modeloInstalado = $m.Nombre
        break
    }
}

if ($modeloInstalado) {
    Write-Host "    OK — modelo presente: $modeloInstalado" -ForegroundColor Green
    $modeloSeleccionado = $modeloInstalado
} else {
    Write-Host "`n    No se detectó ningún modelo instalado. Selecciona uno:`n" -ForegroundColor Yellow
    for ($i = 0; $i -lt $modelos.Count; $i++) {
        Write-Host "    $($i+1). $($modelos[$i].Nombre)  [$($modelos[$i].Tamanio)]  — $($modelos[$i].Descripcion)" -ForegroundColor White
    }
    Write-Host ""
    $seleccion = Read-Host "    Opción (1-4)"
    switch ($seleccion) {
        "1" { $modeloSeleccionado = $modelos[0].Nombre }
        "2" { $modeloSeleccionado = $modelos[1].Nombre }
        "3" { $modeloSeleccionado = $modelos[2].Nombre }
        "4" { $modeloSeleccionado = Read-Host "    Nombre del modelo (ej: mistral:7b)" }
        default { Write-Error "Opción no válida." }
    }
    Write-Host "    Descargando $modeloSeleccionado..." -ForegroundColor Gray
    ollama pull $modeloSeleccionado
    Write-Host "    OK — modelo instalado: $modeloSeleccionado" -ForegroundColor Green
}

# ——————————————————————————
# 5. ENTORNO VIRTUAL PYTHON
# ——————————————————————————
Write-Host "`n[5/7] Verificando entorno virtual..." -ForegroundColor Yellow

$venvPath = Join-Path $root "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "    venv no encontrado o corrupto. Reconstruyendo..." -ForegroundColor Gray
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
    python -m venv $venvPath
}
Write-Host "    OK" -ForegroundColor Green

# ——————————————————————————
# 6. OPEN INTERPRETER
# ——————————————————————————
Write-Host "`n[6/7] Verificando Open Interpreter 0.3.4..." -ForegroundColor Yellow

& $venvActivate
$oiVersion = python -c "import importlib.metadata; print(importlib.metadata.version('open-interpreter'))" 2>&1

if ($oiVersion -ne "0.3.4") {
    Write-Host "    Instalando open-interpreter==0.3.4 (versión fija)..." -ForegroundColor Gray
    python -m pip install --upgrade pip --quiet
    pip install open-interpreter==0.3.4 --quiet
    Write-Host "    ADVERTENCIA: ignorar cualquier aviso de versión más nueva." -ForegroundColor DarkYellow
}
Write-Host "    OK — Open Interpreter 0.3.4" -ForegroundColor Green

# ——————————————————————————
# 7. CONFIG.YAML
# ——————————————————————————
Write-Host "`n[7/7] Verificando config.yaml..." -ForegroundColor Yellow

$configPath = Join-Path $root "config.yaml"
if (-not (Test-Path $configPath)) {
    Write-Host "    config.yaml no encontrado. Generando valores por defecto..." -ForegroundColor Gray
    @"
model: ollama/$modeloSeleccionado
auto_run: false
system_message_path: system.md
sandbox: true
logs_path: logs/
memory_path: memoria/
"@ | Set-Content -Path $configPath -Encoding UTF8
    Write-Host "    Creado config.yaml con valores por defecto." -ForegroundColor Gray
} else {
    Write-Host "    OK — config.yaml existente, no modificado" -ForegroundColor Green
}

# ——————————————————————————
# COMMIT AUTOMÁTICO
# ——————————————————————————
Write-Host "`n[Git] Registrando estado..." -ForegroundColor Yellow

Set-Location $root
$status = git status --porcelain
if ($status) {
    git add -A
    git commit -m "setup.ps1: estado post-instalación $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-Host "    OK — commit realizado" -ForegroundColor Green
} else {
    Write-Host "    OK — sin cambios que registrar" -ForegroundColor Green
}

# ——————————————————————————
# RESULTADO FINAL
# ——————————————————————————
Write-Host "`n=== SETUP COMPLETADO ===" -ForegroundColor Cyan
Write-Host "Para arrancar JARVIS2: .\jarvis.ps1" -ForegroundColor White