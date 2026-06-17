param(
    [string]$ImagePath = ""
)

$ErrorActionPreference = "Stop"

if (-not $ImagePath) {
    Write-Host "ERROR: Debes proporcionar la ruta de una imagen."
    exit 1
}

if (-not (Test-Path $ImagePath)) {
    Write-Host "ERROR: No se encuentra la imagen en: $ImagePath"
    exit 1
}

try {
    # Cargar adaptador de Windows Runtime en .NET
    [void][System.Reflection.Assembly]::LoadWithPartialName("System.Runtime.WindowsRuntime")
    
    # Declarar los tipos
    $storageFileType = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
    $irandomAccessStreamType = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage, ContentType = WindowsRuntime]
    $bitmapDecoderType = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
    $softwareBitmapType = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
    $ocrResultType = [Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType = WindowsRuntime]

    # Helper para ejecutar llamadas asíncronas de WinRT mediante reflexión de AsTask
    function Await-WinRT($asyncOp, $resultType) {
        $asTaskMethods = [System.WindowsRuntimeSystemExtensions].GetMethods()
        $asTask = $asTaskMethods | Where-Object { 
            $_.Name -eq 'AsTask' -and 
            $_.GetParameters().Length -eq 1 -and 
            $_.GetParameters()[0].ParameterType.Name.StartsWith("IAsyncOperation") 
        } | Select-Object -First 1

        if ($null -eq $asTask) {
            throw "No se pudo encontrar el método AsTask genérico en .NET."
        }

        $genericAsTask = $asTask.MakeGenericMethod($resultType)
        $task = $genericAsTask.Invoke($null, @($asyncOp))
        $task.Wait()
        return $task.Result
    }

    # 1. Obtener el archivo
    $asyncFile = [Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)
    $file = Await-WinRT $asyncFile $storageFileType

    # 2. Abrir el flujo
    $asyncStream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = Await-WinRT $asyncStream $irandomAccessStreamType

    # 3. Decodificar el bitmap
    $asyncDecoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = Await-WinRT $asyncDecoder $bitmapDecoderType

    # 4. Obtener el SoftwareBitmap
    $asyncBitmap = $decoder.GetSoftwareBitmapAsync()
    $softwareBitmap = Await-WinRT $asyncBitmap $softwareBitmapType

    # 5. Crear motor de OCR
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) {
        throw "No se pudo crear el motor de OCR nativo de Windows."
    }

    # 6. Reconocer texto
    $asyncOcr = $engine.RecognizeAsync($softwareBitmap)
    $ocrResult = Await-WinRT $asyncOcr $ocrResultType

    # Imprimir resultado limpio
    Write-Output $ocrResult.Text

} catch {
    Write-Error "ERROR en OCR nativo de Windows: $_"
    exit 1
}
