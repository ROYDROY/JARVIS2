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
    # Dividir el patron por espacios para que Everything busque todas las palabras en cualquier orden (operacion AND)
    $argsBusqueda = $PatronBusqueda -split '\s+' | Where-Object { $_ -ne "" }
    $resultados = & $esPath $argsBusqueda -n $LimiteResultados 2>$null
    if ($resultados) {
        foreach ($res in $resultados) {
            Write-Host $res
            $contador++
        }
    }
} else {
    # Si no esta Everything, hacemos busqueda recursiva y filtramos que contenga todas las palabras (operacion AND)
    $filtros = $PatronBusqueda -split '\s+' | Where-Object { $_ -ne "" }
    Get-ChildItem -Path $RutaBase -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $fullName = $_.FullName
        $match = $true
        foreach ($f in $filtros) {
            if ($fullName -notlike "*$f*") {
                $match = $false
                break
            }
        }
        $match
    } | ForEach-Object {
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
