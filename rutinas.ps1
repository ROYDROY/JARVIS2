param (
    [string]$Tarea = "Revisa el estado general del sistema y guárdalo en C:\JARVIS2\sandbox\estado_rutina.txt"
)

# ----- ARRANQUE OLLAMA (DEMONIO) -----
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
$timeout = 15
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
while ($stopwatch.Elapsed.TotalSeconds -lt $timeout) {
    try {
        $tcpConnection = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 11434)
        $tcpConnection.Close()
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
$stopwatch.Stop()

$pythonPath = "C:\JARVIS2\venv\Scripts\python.exe"
$scriptPath = "C:\JARVIS2\proactivo.py"

Write-Host "Lanzando rutina en segundo plano: '$Tarea'" -ForegroundColor Cyan
Write-Host "Puedes seguir trabajando. Si algo sale mal, usa el botón del pánico en el escritorio." -ForegroundColor Yellow

# Iniciar proceso en segundo plano de forma totalmente invisible
Start-Process -FilePath $pythonPath -ArgumentList "`"$scriptPath`" `"$Tarea`"" -WindowStyle Hidden

Write-Host "Rutina enviada a JARVIS." -ForegroundColor Green
