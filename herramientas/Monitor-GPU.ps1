# Script de monitorización de GPU para JARVIS2
$salida = nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit --format=csv,noheader,nounits

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo ejecutar nvidia-smi. ¿Están instalados los drivers de NVIDIA?"
    exit 1
}

$datos = $salida -split ', '
$gpu = [PSCustomObject]@{
    Nombre = $datos[0]
    Temperatura = "$($datos[1]) C"
    UsoGPU = "$($datos[2]) %"
    VRAM_Usada = "$([math]::Round($datos[3] / 1024, 2)) GB"
    VRAM_Total = "$([math]::Round($datos[4] / 1024, 2)) GB"
    Consumo_W = "$($datos[5]) W / $($datos[6]) W"
}

Write-Host "=== ESTADO DE LA GPU ===" -ForegroundColor Cyan
$gpu | Format-List | Out-String | Write-Host
