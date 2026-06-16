param (
    [Parameter(Mandatory=$true)]
    [string]$directorio
)

Write-Host "Iniciando ingesta masiva en: $directorio"
$archivos = Get-ChildItem -Path $directorio -Filter "*.md" -Recurse

$total = $archivos.Count
$actual = 1

foreach ($archivo in $archivos) {
    Write-Host "[$actual/$total] Ingestando $($archivo.Name)..."
    # Ejecutamos el gestor de memoria
    $p = Start-Process -FilePath "C:\JARVIS2\venv\Scripts\python.exe" -ArgumentList "C:\JARVIS2\herramientas\Gestor-Memoria.py `"$($archivo.FullName)`"" -Wait -NoNewWindow
    $actual++
}

Write-Host "Ingesta completada."
