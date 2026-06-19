# setup.ps1 -- JARVIS2
# Uso: git clone <repo> && cd <repo> && .\setup.ps1
# Levanta el sistema completo en maquina limpia sin pasos manuales.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Check-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Host "`n==== JARVIS2 SETUP ====" -ForegroundColor Cyan

# ------------------------------
# 0. WINGET
# ------------------------------
Write-Host "`n[0/7] Verificando winget..." -ForegroundColor Yellow
if (-not (Check-Command winget)) {
    Write-Host ""
    Write-Host "  ERROR: winget no encontrado en este sistema." -ForegroundColor Red
    Write-Host "  Sin winget no se pueden instalar dependencias automaticamente." -ForegroundColor Red
    Write-Host "  Solucion: instala App Installer desde Microsoft Store y vuelve a ejecutar setup.ps1." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Pulsa Enter para salir"
    exit 1
}
Write-Host "    OK -- winget disponible" -ForegroundColor Green

# ------------------------------
# 1. POWERSHELL 7
# ------------------------------
Write-Host "`n[1/7] Verificando PowerShell 7..." -ForegroundColor Yellow
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwshCmd) {
        $pwshExe = $pwshCmd.Source
        Write-Host "    PowerShell 7 disponible. Relanzando en pwsh.exe..." -ForegroundColor Gray
    } else {
        Write-Host "    PowerShell 7 no encontrado. Instalando via winget (obligatorio)..." -ForegroundColor Gray
        winget install Microsoft.PowerShell --silent --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
        if (-not $pwshCmd) {
            Write-Host ""
            Write-Host "  ERROR: Instalacion de PowerShell 7 fallida." -ForegroundColor Red
            Write-Host "  Instala manualmente desde https://aka.ms/PSWindows y vuelve a ejecutar setup.ps1." -ForegroundColor Yellow
            Read-Host "  Pulsa Enter para salir"
            exit 1
        }
        $pwshExe = $pwshCmd.Source
        Write-Host "    OK -- PowerShell 7 instalado" -ForegroundColor Green
    }
    Start-Process $pwshExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Wait
    exit
}
Write-Host "    OK -- PS $($PSVersionTable.PSVersion)" -ForegroundColor Green

# ------------------------------
# 1B. PYTHON 3.10+
# ------------------------------
Write-Host "`n    Verificando Python 3.10+..." -ForegroundColor Yellow
$pythonOk = $false
if (Check-Command python) {
    $pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ([version]$pyVersion -ge [version]"3.10") {
        $pythonOk = $true
        Write-Host "    OK -- Python $pyVersion" -ForegroundColor Green
    } else {
        Write-Host "    Python $pyVersion detectado -- se requiere 3.10+. Instalando..." -ForegroundColor Gray
    }
}
if (-not $pythonOk) {
    Write-Host "    Python 3.10 no encontrado. Instalando via winget (obligatorio)..." -ForegroundColor Gray
    winget install Python.Python.3.10 --silent --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    if (-not (Check-Command python)) {
        Write-Host ""
        Write-Host "  ERROR: Instalacion de Python 3.10 fallida." -ForegroundColor Red
        Write-Host "  Instala manualmente desde https://www.python.org/downloads/release/python-31011/ y vuelve a ejecutar." -ForegroundColor Yellow
        Read-Host "  Pulsa Enter para salir"
        exit 1
    }
    Write-Host "    OK -- Python instalado" -ForegroundColor Green
}

# ------------------------------
# 1C. GIT
# ------------------------------
Write-Host "`n    Verificando Git..." -ForegroundColor Yellow
if (-not (Check-Command git)) {
    Write-Host "    Git no encontrado. Instalando via winget (obligatorio)..." -ForegroundColor Gray
    winget install Git.Git --silent --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    if (-not (Check-Command git)) {
        Write-Host ""
        Write-Host "  ERROR: Instalacion de Git fallida." -ForegroundColor Red
        Write-Host "  Instala manualmente desde https://git-scm.com/download/win y vuelve a ejecutar." -ForegroundColor Yellow
        Read-Host "  Pulsa Enter para salir"
        exit 1
    }
    Write-Host "    OK -- Git instalado" -ForegroundColor Green
} else {
    Write-Host "    OK -- $(git --version)" -ForegroundColor Green
}

# ------------------------------
# 1D. ESPACIO EN DISCO (12 GB minimo)
# ------------------------------
Write-Host "`n    Verificando espacio en disco..." -ForegroundColor Yellow
$drive = Split-Path $root -Qualifier
$freeGB = [math]::Round((Get-PSDrive ($drive.TrimEnd(':'))).Free / 1GB, 1)
if ($freeGB -lt 12) {
    Write-Host ""
    Write-Host "  ERROR: Espacio insuficiente. Disponible: $freeGB GB. Minimo: 12 GB." -ForegroundColor Red
    Read-Host "  Pulsa Enter para salir"
    exit 1
}
Write-Host "    OK -- Disco libre: $freeGB GB" -ForegroundColor Green

# ------------------------------
# 2. ESTRUCTURA DE CARPETAS
# ------------------------------
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

# ------------------------------
# 3. OLLAMA
# ------------------------------
Write-Host "`n[3/7] Verificando Ollama..." -ForegroundColor Yellow
if (-not (Check-Command ollama)) {
    Write-Host "    Ollama no encontrado. Instalando via winget..." -ForegroundColor Gray
    winget install Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    if (-not (Check-Command ollama)) {
        Write-Host ""
        Write-Host "  ERROR: Instalacion de Ollama fallida. Instalalo manualmente desde https://ollama.com" -ForegroundColor Red
        Read-Host "  Pulsa Enter para salir"
        exit 1
    }
}
Write-Host "    OK -- $(ollama --version)" -ForegroundColor Green

# ------------------------------
# ------------------------------
# 4. MODELOS (MoE DINÁMICO)
# ------------------------------
Write-Host "`n[4/7] Evaluando Hardware para Modelos MoE..." -ForegroundColor Yellow

$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)
Write-Host "    Memoria RAM detectada: $ramGB GB" -ForegroundColor Gray

if ($ramGB -ge 32) {
    Write-Host "    Tier 1 (Ferrari): Asignando qwen2.5-coder:14b (Codigo) y llama3.1:8b (Chat)." -ForegroundColor Green
    $modelCoder = "qwen2.5-coder:14b"
    $modelChat = "llama3.1:8b"
} elseif ($ramGB -ge 16) {
    Write-Host "    Tier 2 (Berlina): Asignando qwen2.5:7b (Universal)." -ForegroundColor Yellow
    $modelCoder = "qwen2.5:7b"
    $modelChat = "qwen2.5:7b"
} else {
    Write-Host "    Tier 3 (Patinete): Asignando qwen2.5:3b (Ultra ligero)." -ForegroundColor DarkYellow
    $modelCoder = "qwen2.5:3b"
    $modelChat = "qwen2.5:3b"
}

$modelEmbed = "nomic-embed-text"

$modelosRequeridos = @($modelCoder, $modelChat, $modelEmbed) | Select-Object -Unique
$modelList = ollama list 2>&1

foreach ($m in $modelosRequeridos) {
    if ($modelList -match $m) {
        Write-Host "    OK -- modelo presente: $m" -ForegroundColor Green
    } else {
        Write-Host "    Descargando $m (puede tardar varios minutos)..." -ForegroundColor Gray
        ollama pull $m
        Write-Host "    OK -- modelo instalado: $m" -ForegroundColor Green
    }
}

# ------------------------------
# 5. ENTORNO VIRTUAL PYTHON
# ------------------------------
Write-Host "`n[5/7] Verificando entorno virtual..." -ForegroundColor Yellow

$venvPath     = Join-Path $root "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython   = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "    venv no encontrado o corrupto. Reconstruyendo..." -ForegroundColor Gray
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
    python -m venv $venvPath
}
Write-Host "    OK" -ForegroundColor Green

# ------------------------------
# 6. OPEN INTERPRETER
# ------------------------------
Write-Host "`n[6/7] Verificando Open Interpreter 0.3.4..." -ForegroundColor Yellow

& $venvActivate
$oiVersion = python -c "import importlib.metadata; print(importlib.metadata.version('open-interpreter'))" 2>&1

if ($oiVersion -ne "0.3.4") {
    Write-Host "    Instalando dependencias base (Open Interpreter, ChromaDB, GUI, Gemini MoE)..." -ForegroundColor Gray
    python -m pip install --upgrade pip --quiet
    pip install open-interpreter==0.3.4 chromadb customtkinter SpeechRecognition PyAudio python-dotenv duckduckgo-search pynput keyboard pyautogui windnd requests pyyaml pillow --quiet
    Write-Host "    ADVERTENCIA: ignorar cualquier aviso de version mas nueva." -ForegroundColor DarkYellow
}
Write-Host "    OK -- Open Interpreter 0.3.4" -ForegroundColor Green

# ------------------------------
# 7. CONFIG.YAML
# ------------------------------
Write-Host "`n[7/7] Verificando config.yaml..." -ForegroundColor Yellow

$configPath = Join-Path $root "config.yaml"
if (-not (Test-Path $configPath)) {
    Write-Host "    config.yaml no encontrado. Generando valores por defecto..." -ForegroundColor Gray
    @"
model_coder: ollama/$modelCoder
model_chat: ollama/$modelChat
auto_run: false
system_message_path: system.md
sandbox: true
logs_path: logs/
memory_path: memoria/
"@ | Set-Content -Path $configPath -Encoding UTF8
    Write-Host "    Creado config.yaml con valores por defecto adaptados a tu hardware." -ForegroundColor Gray
} else {
    Write-Host "    config.yaml existente detectado. Actualizando modelos..." -ForegroundColor Gray
    $configContent = Get-Content $configPath -Raw
    $configContent = $configContent -replace "(?m)^model:.*`r?`n", ""
    $configContent = $configContent -replace "(?m)^model_coder:.*`r?`n", ""
    $configContent = $configContent -replace "(?m)^model_chat:.*`r?`n", ""
    
    $newModels = "model_coder: ollama/$modelCoder`nmodel_chat: ollama/$modelChat`n"
    $newModels + $configContent | Set-Content -Path $configPath -Encoding UTF8
    Write-Host "    OK -- config.yaml actualizado con los modelos MoE." -ForegroundColor Green
}

# ------------------------------
# 7B. INDICE.JSON
# ------------------------------
Write-Host "`n[7B] Verificando indice.json..." -ForegroundColor Yellow

$indicePath = Join-Path $root "indice.json"
if (-not (Test-Path $indicePath)) {
    Write-Host "    indice.json no encontrado. Generando valores por defecto..." -ForegroundColor Gray
    $indiceDefault = @{
        apps_uwp = @{
            whatsapp = @{
                open = "shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
                close_cmd = "Get-Process | Where-Object {`$_.Name -like '*WhatsApp*'} | Stop-Process -Force"
            }
            whatsappdesktop = @{
                open = "shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
                close_cmd = "Get-Process | Where-Object {`$_.Name -like '*WhatsApp*'} | Stop-Process -Force"
            }
            spotify = @{
                open = "shell:AppsFolder\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify"
                close_title = "Spotify"
            }
        }
        apps_custom = @{
            autofirma = @{
                open = "C:\Program Files\Autofirma\Autofirma\Autofirma.exe"
                close_title = "Autofirma"
            }
            x = @{ nombres = @("x", "twitter"); lnk = $true }
            discord = @{ nombres = @("discord"); lnk = $true }
            instagram = @{ nombres = @("instagram", "insta"); lnk = $true }
            tiktok = @{ nombres = @("tiktok", "tik tok"); lnk = $true }
            linkedin = @{ nombres = @("linkedin"); lnk = $true }
            substack = @{ nombres = @("substack"); lnk = $true }
            facebook = @{ nombres = @("facebook", "fb"); lnk = $true }
            telegram = @{ nombres = @("telegram"); lnk = $true }
        }
    }
    $indiceDefault | ConvertTo-Json -Depth 5 | Set-Content -Path $indicePath -Encoding UTF8
    Write-Host "    Creado indice.json con valores por defecto." -ForegroundColor Green
} else {
    Write-Host "    OK -- indice.json ya existe" -ForegroundColor Green
}

# ------------------------------
# COMMIT AUTOMATICO
# ------------------------------
Write-Host "`n[Git] Registrando estado..." -ForegroundColor Yellow

Set-Location $root
$isRepo = git rev-parse --is-inside-work-tree 2>$null
if (-not $isRepo) {
    Write-Host "    AVISO -- no es un repositorio git. Omitiendo commit." -ForegroundColor Yellow
} else {
    $status = git status --porcelain
    if ($status) {
        git add -A
        git commit -m "setup.ps1: estado post-instalacion $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-Host "    OK -- commit realizado" -ForegroundColor Green
    } else {
        Write-Host "    OK -- sin cambios que registrar" -ForegroundColor Green
    }
}

# ------------------------------
# RESULTADO FINAL
# ------------------------------
Write-Host "`n==== SETUP COMPLETADO ====" -ForegroundColor Cyan
Write-Host "Para arrancar JARVIS2: Ejecuta lanzar_silencioso.vbs o el acceso directo del Escritorio" -ForegroundColor White


