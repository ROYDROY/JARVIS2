param(
    [string]$RutaDestino = "",
    [string]$Formato = "pdf",
    [switch]$Interactivo
)

# Load Windows Forms for GUI dialogs
Add-Type -AssemblyName System.Windows.Forms

# Convert target format to lowercase
$Formato = $Formato.ToLower()
if ($Formato -ne "pdf" -and $Formato -ne "bmp" -and $Formato -ne "jpg") { $Formato = "pdf" }

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
        [System.Windows.Forms.MessageBox]::Show("No se encontró ningún escáner conectado o encendido. Abriendo el asistente de Windows...", "JARVIS - Escáner", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null
        Start-InteractiveScan
    }

    Write-Host "[INFO] Conectando al primer escáner disponible..."
    $device = $deviceManager.DeviceInfos.Item(1).Connect()

    $tempFiles = @()
    $pageCounter = 1
    $continueScanning = $true

    while ($continueScanning) {
        Write-Host "[INFO] Escaneando página $pageCounter..."
        
        # Connect to the scanner item
        $item = $device.Items.Item(1)
        $image = $item.Transfer()

        # Save to temp BMP
        $tempBmp = [System.IO.Path]::GetTempFileName() + ".bmp"
        if (Test-Path $tempBmp) { Remove-Item $tempBmp -Force }
        $image.SaveFile($tempBmp)
        
        $tempFiles += $tempBmp
        Write-Host "[INFO] Página $pageCounter escaneada temporalmente."

        # Ask if the user wants to scan more pages
        $msgResult = [System.Windows.Forms.MessageBox]::Show("¿Quieres escanear otra hoja para este documento?", "JARVIS - Escáner", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
        
        if ($msgResult -eq [System.Windows.Forms.DialogResult]::Yes) {
            $nextPrompt = [System.Windows.Forms.MessageBox]::Show("Coloca la siguiente hoja en el escáner y pulsa Aceptar para continuar.", "JARVIS - Escáner", [System.Windows.Forms.MessageBoxButtons]::OKCancel, [System.Windows.Forms.MessageBoxIcon]::Information)
            if ($nextPrompt -eq [System.Windows.Forms.DialogResult]::Cancel) {
                $continueScanning = $false
            } else {
                $pageCounter++
            }
        } else {
            $continueScanning = $false
        }
    }

    # Now process the collected temporary files
    if ($tempFiles.Count -eq 0) {
        Write-Host "[ERROR] No se escaneó ninguna página."
        exit 1
    }

    Write-Host "[INFO] Procesando y guardando escaneo..."
    if ($Formato -eq "bmp") {
        if ($tempFiles.Count -eq 1) {
            if (Test-Path $RutaDestino) { Remove-Item $RutaDestino -Force }
            Move-Item -Path $tempFiles[0] -Destination $RutaDestino -Force
            Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
        } else {
            for ($i = 0; $i -lt $tempFiles.Count; $i++) {
                $dest = $RutaDestino -replace '\.bmp$', "_$($i+1).bmp"
                if (Test-Path $dest) { Remove-Item $dest -Force }
                Move-Item -Path $tempFiles[$i] -Destination $dest -Force
            }
            Write-Host "SUCCESS: Escaneos guardados con sufijo de página en la ruta: $RutaDestino"
        }
    }
    elseif ($Formato -eq "jpg") {
        $imageProcess = New-Object -ComObject WIA.ImageProcess
        $imageProcess.Filters.Add($imageProcess.FilterInfos.Item("Convert").FilterID)
        $imageProcess.Filters.Item(1).Properties.Item("FormatID").Value = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
        $imageProcess.Filters.Item(1).Properties.Item("Quality").Value = 85

        for ($i = 0; $i -lt $tempFiles.Count; $i++) {
            $dest = $RutaDestino
            if ($tempFiles.Count -gt 1) {
                $dest = $RutaDestino -replace '\.jpg$', "_$($i+1).jpg"
            }
            
            $tempImg = New-Object -ComObject WIA.ImageFile
            $tempImg.LoadFile($tempFiles[$i])
            $jpgImage = $imageProcess.Apply($tempImg)
            
            if (Test-Path $dest) { Remove-Item $dest -Force }
            $jpgImage.SaveFile($dest)
            Remove-Item $tempFiles[$i] -Force
        }
        Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
    }
    elseif ($Formato -eq "pdf") {
        Write-Host "[INFO] Convirtiendo páginas a un único PDF..."
        
        # Clean paths for python compatibility
        $cleanTempFiles = $tempFiles | ForEach-Object { $_ -replace '\\', '/' }
        $cleanDest = $RutaDestino -replace '\\', '/'
        
        # Format the list of files as a Python list string
        $filesListStr = "[" + (($cleanTempFiles | ForEach-Object { "'$_'" }) -join ", ") + "]"
        
        $pythonPath = "C:\JARVIS2\venv\Scripts\python.exe"
        $cmd = "from PIL import Image; files=$filesListStr; imgs=[Image.open(f) for f in files]; imgs[0].save('$cleanDest', 'PDF', save_all=True, append_images=imgs[1:])"
        
        & $pythonPath -c $cmd
        
        if (Test-Path $RutaDestino) {
            Write-Host "SUCCESS: Escaneo guardado en: $RutaDestino"
        } else {
            Write-Host "[ERROR] La conversión a PDF falló. Guardando como BMPs individuales."
            for ($i = 0; $i -lt $tempFiles.Count; $i++) {
                $dest = $RutaDestino -replace '\.pdf$', "_$($i+1).bmp"
                if (Test-Path $dest) { Remove-Item $dest -Force }
                Move-Item -Path $tempFiles[$i] -Destination $dest -Force
            }
        }
        
        # Cleanup temp files
        foreach ($f in $tempFiles) {
            if (Test-Path $f) { Remove-Item $f -Force }
        }
    }

    # Open the scanned document in Adobe Acrobat Pro automatically!
    if (Test-Path $RutaDestino) {
        Write-Host "[INFO] Abriendo el documento escaneado en Acrobat Pro..."
        $acrobatPath = "C:\Program Files (x86)\Adobe\Acrobat 11.0\Acrobat\Acrobat.exe"
        if (Test-Path $acrobatPath) {
            Start-Process -FilePath $acrobatPath -ArgumentList "`"$RutaDestino`""
        } else {
            Start-Process -FilePath $RutaDestino
        }
    }
}
catch {
    Write-Host "[ERROR] Ocurrió un error durante el escaneo: $_"
    [System.Windows.Forms.MessageBox]::Show("Ocurrió un error durante el escaneo automático: $_. Abriendo el asistente de Windows...", "JARVIS - Escáner", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    Start-InteractiveScan
}
