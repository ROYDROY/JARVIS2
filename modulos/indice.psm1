# ============================================================
# JARVIS2 — Módulo INDICE v1.1
# Escanea capa caliente de forma INCREMENTAL y escribe memoria\indice.json
# Cumple el Contrato de Módulo v1.0
# ============================================================

$ModuloMetadata = @{
    Nombre = "indice"
    Version = "1.1"
    Descripcion = "Módulo de indexación del sistema (Incremental)"
}

function Update-Indice {
    param (
        [string]$RutaBase = "C:\JARVIS2"
    )
    try {
        $rutaSalida = Join-Path $RutaBase "memoria\indice.json"
        $requiereEscaneoProfundo = $true
        $indiceAnterior = $null

        if (Test-Path $rutaSalida) {
            $fechaMod = (Get-Item $rutaSalida).LastWriteTime
            # Si el índice tiene menos de 24 horas, escaneo incremental (solo discos)
            if ($fechaMod -gt (Get-Date).AddHours(-24)) {
                $requiereEscaneoProfundo = $false
                $indiceAnterior = Get-Content $rutaSalida -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue
                if (-not $indiceAnterior -or -not $indiceAnterior.apps_instaladas) { 
                    $requiereEscaneoProfundo = $true 
                }
            }
        }

        # --- DISCOS (Se actualiza siempre, es muy rápido) ---
        $discos = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' } | ForEach-Object {
            [PSCustomObject]@{
                letra    = $_.Root
                etiqueta = if ($_.Description) { $_.Description } else { "" }
                libre_gb = [math]::Round($_.Free / 1GB, 2)
                total_gb = [math]::Round(($_.Used + $_.Free) / 1GB, 2)
            }
        }

        if ($requiereEscaneoProfundo) {
            # --- CARPETAS RAIZ DEL USUARIO (sin carpetas ocultas) ---
            $carpetasUsuario = Get-ChildItem -Path $env:USERPROFILE -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -notmatch '^\.' } |
                Select-Object -ExpandProperty FullName

            # --- APPS INSTALADAS ---
            $registros = @(
                "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
                "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
                "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
            )

            $apps = foreach ($ruta in $registros) {
                if (Test-Path $ruta) {
                    Get-ItemProperty $ruta -ErrorAction SilentlyContinue |
                        Where-Object { $_.DisplayName } |
                        Select-Object -ExpandProperty DisplayName
                }
            }
            $apps = $apps | Sort-Object -Unique
        } else {
            # Recuperar de la caché
            $carpetasUsuario = $indiceAnterior.carpetas_usuario
            $apps = $indiceAnterior.apps_instaladas
        }

        # --- CONSTRUIR OBJETO ---
        $indice = [PSCustomObject]@{
            generado         = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
            tipo_actualizacion = if ($requiereEscaneoProfundo) { "Completa" } else { "Incremental" }
            discos           = $discos
            carpetas_usuario = $carpetasUsuario
            apps_instaladas  = $apps
        }

        # --- GUARDAR JSON (UTF-8 sin BOM) ---
        $json = $indice | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($rutaSalida, $json, [System.Text.UTF8Encoding]::new($false))
        
        return $true
    } catch {
        Write-Error "[Módulo Índice] Fallo crítico interno: $_"
        return $false
    }
}

Export-ModuleMember -Function Update-Indice -Variable ModuloMetadata

# Auto-ejecución en el arranque (Carga del módulo)
Update-Indice
