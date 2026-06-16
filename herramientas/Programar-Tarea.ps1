param (
    [Parameter(Mandatory=$true)]
    [string]$Hora,      # Ejemplo: "08:00" o "14:30"
    
    [Parameter(Mandatory=$true)]
    [string]$Tarea,     # Ejemplo: "Revisa Fenix y dame un resumen"
    
    [string]$NombreTarea = "JARVIS_Rutina_Proactiva"
)

$ErrorActionPreference = "Stop"
Write-Host "Programando rutina de JARVIS para las $Hora..." -ForegroundColor Cyan

# 1. Crear la Acción: Llamar a rutinas.ps1
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File C:\JARVIS2\rutinas.ps1 -Tarea `"$Tarea`""

# 2. Crear el Disparador: Todos los días a la hora indicada
$trigger = New-ScheduledTaskTrigger -Daily -At $Hora

# 3. Registrar la tarea (sobrescribe si ya existe una con el mismo nombre)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $NombreTarea -Description "Rutina programada por JARVIS2: $Tarea" -Force | Out-Null

Write-Host "¡Rutina '$Tarea' programada con éxito a las $Hora!" -ForegroundColor Green
