param(
    [string]$RutaDestino = "",
    [string]$Formato = "jpg",
    [switch]$Interactivo
)

# Convert target format to lowercase
$Formato = $Formato.ToLower()
if ($Formato -ne "pdf" -and $Formato -ne "bmp") { $Formato = "jpg" }

# If destination path is not specified, default to Desktop
if ([string]::IsNullOrEmpty($RutaDestino)) {
    $fecha = Get-Date -Format "yyyyMMdd_HHmmss"
    $desktop = [Environment]::GetFolderPath("Desktop")
    $ext = $Formato
    $RutaDestino = Join-Path $desktop "Escaneo_$fecha.$ext"
}

# Ensure destination directory exists
$dir = Split-Path -Parent $RutaDestino
if ($dir -and -not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Function to run wiaacmgr.exe as a fallback
function Start-InteractiveScan {
    Write-Host "[INFO] Abriendo el Asistente de Escaneo interactivo de Windows (wiaacmgr.exe)..."
    Start-Process -FilePath "C:\WINDOWS\system32\wiaacmgr.exe"
    exit 0
}

# If interactive switch is passed, run and exit
if ($Interactivo) {
    Start-InteractiveScan
}

try {
    Write-Host "[INFO] Detectando dispositivos WIA..."
    $deviceManager = New-Object -ComObject WIA.DeviceManager
    $count = $deviceManager.DeviceInfos.Count
    if ($count -eq 0) {
        Write-Host "[ADVERTENCIA] No se encontró ningún escáner conectado o encendido."
        Start-InteractiveScan
    }

    Write-Host "[INFO] Conectando al primer escáner disponible..."
    $device = $deviceManager.DeviceInfos.Item(1).Connect()
    
    Write-Host "[INFO] Escaneando documento..."
    $item = $device.Items.Item(1)
    $image = $item.Transfer()

    # Save to a temporary BMP first
    $tempBmp = [System.IO.Path]::GetTempFileName() + ".bmp"
    # Ensure temp file does not exist so WIA can write to it
    if (Test-Path $tempBmp) { Remove-Item $tempBmp -Force }
    
    $image.SaveFile($tempBmp)

    # Perform conversions
    if ($Formato -eq "bmp") {
        if (Test-Path $RutaDestino) { Remove-Item $RutaDestino -Force }
        Move-Item -Path $tempBmp -Destination $RutaDestino -Force
        Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
    }
    elseif ($Formato -eq "jpg") {
        Write-Host "[INFO] Convirtiendo imagen a JPEG..."
        $imageProcess = New-Object -ComObject WIA.ImageProcess
        $imageProcess.Filters.Add($imageProcess.FilterInfos.Item("Convert").FilterID)
        $imageProcess.Filters.Item(1).Properties.Item("FormatID").Value = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
        $imageProcess.Filters.Item(1).Properties.Item("Quality").Value = 85
        
        $tempImg = New-Object -ComObject WIA.ImageFile
        $tempImg.LoadFile($tempBmp)
        $jpgImage = $imageProcess.Apply($tempImg)
        
        if (Test-Path $RutaDestino) { Remove-Item $RutaDestino -Force }
        $jpgImage.SaveFile($RutaDestino)
        
        # Cleanup temp BMP
        Remove-Item $tempBmp -Force
        Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
    }
    elseif ($Formato -eq "pdf") {
        Write-Host "[INFO] Convirtiendo imagen a PDF..."
        
        # Convert path to use forward slashes for python compatibility
        $cleanTempBmp = $tempBmp -replace '\\', '/'
        $cleanDest = $RutaDestino -replace '\\', '/'
        
        $pythonPath = "C:\JARVIS2\venv\Scripts\python.exe"
        $cmd = "from PIL import Image; Image.open('$cleanTempBmp').save('$cleanDest', 'PDF')"
        
        & $pythonPath -c $cmd
        
        if (Test-Path $RutaDestino) {
            Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
        } else {
            Write-Host "[ERROR] La conversión a PDF falló. Guardando como BMP en su lugar."
            $fallbackDest = $RutaDestino -replace '\.pdf$', '.bmp'
            if (Test-Path $fallbackDest) { Remove-Item $fallbackDest -Force }
            Move-Item -Path $tempBmp -Destination $fallbackDest -Force
            Write-Host "SUCCESS: Escaneo guardado en: $fallbackDest"
        }
        
        # Cleanup temp BMP
        if (Test-Path $tempBmp) { Remove-Item $tempBmp -Force }
    }
}
catch {
    Write-Host "[ERROR] Ocurrió un error durante el escaneo automático: $_"
    Start-InteractiveScan
}
