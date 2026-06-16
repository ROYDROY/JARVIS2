# PANIC BUTTON - Freno de emergencia para JARVIS2
$ErrorActionPreference = "SilentlyContinue"

# 1. Matar el ejecutable principal
Stop-Process -Name "jarvis" -Force

# 2. Matar cualquier proceso de Python que provenga de C:\JARVIS2
$pythonProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'"
foreach ($proc in $pythonProcesses) {
    if ($proc.ExecutablePath -like "C:\JARVIS2*") {
        Stop-Process -Id $proc.ProcessId -Force
    }
}

# 3. Notificación visual al usuario
$ErrorActionPreference = "Continue" # Restaurar para ver errores visuales si los hay
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show("SISTEMA COMPROMETIDO INTERRUMPIDO.`n`nTodos los procesos de JARVIS y Python en segundo plano han sido eliminados de la memoria RAM.", "JARVIS - BOTON DEL PANICO", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
