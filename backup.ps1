param(
    [string]$RutaDestino = "",
    [switch]$Silencioso
)

$ErrorActionPreference = "Stop"
$sourceDir = "C:\JARVIS2"

# Verificar que el directorio origen existe
if (-not (Test-Path $sourceDir)) {
    Write-Host "ERROR: No se encuentra la carpeta origen $sourceDir" -ForegroundColor Red
    exit 1
}

# Obtener ruta de destino predeterminada (unidad D de seguridad como prioridad, Escritorio como fallback)
$defaultBackupPath = "D:\DISCOS SEGURIDAD\PROGRAMAS ESCRITORIO\IA\JARVIS"
if (-not (Test-Path $defaultBackupPath)) {
    $defaultBackupPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
}

Write-Host "`n==== COPIA DE SEGURIDAD: JARVIS 4.0 ====" -ForegroundColor Cyan
Write-Host "Este script creará un paquete ZIP del código de JARVIS" -ForegroundColor Gray
Write-Host "excluyendo entornos virtuales (venv), repositorio git e instaladores.`n" -ForegroundColor Gray

# Determinar ruta de destino de la copia
$destinationDir = $RutaDestino
if ([string]::IsNullOrWhiteSpace($destinationDir)) {
    if ($Silencioso) {
        $destinationDir = $defaultBackupPath
    } else {
        $destinationDir = Read-Host "Introduce la ruta para guardar el backup (Pulsa Enter para usar la ruta por defecto: $defaultBackupPath)"
        if ([string]::IsNullOrWhiteSpace($destinationDir)) {
            $destinationDir = $defaultBackupPath
        }
    }
}

# Asegurar que el directorio de destino existe
if (-not (Test-Path $destinationDir)) {
    try {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    } catch {
        Write-Host "ERROR: No se pudo crear el directorio de destino: $destinationDir" -ForegroundColor Red
        exit 1
    }
}

# Nombre del archivo ZIP de salida
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$zipName = "JARVIS2_STABLE_$timestamp.zip"
$zipPath = Join-Path $destinationDir $zipName

# Carpeta temporal para empaquetar
$tempBackupDir = Join-Path $env:TEMP "JARVIS_BACKUP_TEMP_$timestamp"

try {
    Write-Host "1. Preparando copia temporal..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $tempBackupDir -Force | Out-Null

    # Copiar todos los archivos y carpetas del origen al temporal
    # Usaremos Robocopy que es nativo de Windows y ultra-eficiente, permitiendo exclusiones directas
    $excludeDirs = @("venv", "venv_browser", ".git", ".vscode", "node_modules", "__pycache__", "installer", "sandbox")
    $excludeFiles = @("*.zip", "*.tmp", "error.log")

    Write-Host "   Copiando archivos fuentes activos (excluyendo venv, .git, etc.)..." -ForegroundColor Gray
    
    # Robocopy devuelve códigos de salida no estándar. Un valor menor que 8 significa éxito.
    $robocopyParams = @(
        $sourceDir,
        $tempBackupDir,
        "/E",
        "/XD"
    ) + $excludeDirs + @("/XF") + $excludeFiles + @("/NFL", "/NDL", "/NJH", "/NJS")
    
    # Ejecutar robocopy de forma segura
    $process = Start-Process robocopy -ArgumentList $robocopyParams -NoNewWindow -PassThru -Wait
    
    if ($process.ExitCode -ge 8) {
        throw "Robocopy falló al copiar los archivos (código de salida: $($process.ExitCode))."
    }

    Write-Host "2. Comprimiendo archivos en ZIP..." -ForegroundColor Yellow
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path "$tempBackupDir\*" -DestinationPath $zipPath -Force
    
    $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
    Write-Host "`n✅ Copia de seguridad creada con éxito!" -ForegroundColor Green
    Write-Host "   Ubicación: $zipPath" -ForegroundColor White
    Write-Host "   Tamaño: $zipSize MB" -ForegroundColor White

} catch {
    Write-Host "`n❌ ERROR al realizar la copia de seguridad: $_" -ForegroundColor Red
} finally {
    # Limpiar directorio temporal
    if (Test-Path $tempBackupDir) {
        Write-Host "3. Limpiando archivos temporales..." -ForegroundColor Gray
        Remove-Item -Recurse -Force $tempBackupDir -ErrorAction SilentlyContinue | Out-Null
    }
}

if (-not $Silencioso) {
    Write-Host "`nPresiona cualquier tecla para terminar..." -ForegroundColor Gray
    $null = [Console]::ReadKey($true)
}
