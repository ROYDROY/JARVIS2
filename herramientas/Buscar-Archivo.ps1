param (
    [Parameter(Mandatory=$true)]
    [string]$PatronBusqueda,

    [Parameter(Mandatory=$false)]
    [string]$RutaBase = "C:\",

    [Parameter(Mandatory=$false)]
    [int]$LimiteResultados = 50
)

Write-Host "Buscando '$PatronBusqueda' en '$RutaBase' (Max: $LimiteResultados resultados)..." -ForegroundColor Cyan

# Usamos un bloque try-catch para no reventar con accesos denegados
$contador = 0
$errores = 0

$esPath = "C:\JARVIS2\herramientas\es.exe"
if (Test-Path $esPath) {
    Write-Host "Usando Everything (es.exe) para busqueda ultra-rapida..." -ForegroundColor Cyan
    $resultados = & $esPath $PatronBusqueda -n $LimiteResultados 2>$null
    if ($resultados) {
        foreach ($res in $resultados) {
            Write-Host $res
            $contador++
        }
    }
} else {
    Get-ChildItem -Path $RutaBase -Filter "*$PatronBusqueda*" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        if ($contador -lt $LimiteResultados) {
            Write-Host $_.FullName
            $contador++
        }
    }
}

if ($contador -eq 0) {
    Write-Host "No se encontraron resultados para '$PatronBusqueda'." -ForegroundColor Yellow
} else {
    Write-Host "`nMostrando $contador resultados (Límite: $LimiteResultados)." -ForegroundColor Green
}
