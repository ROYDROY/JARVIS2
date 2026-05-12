# ============================================================
# JARVIS2 — Módulo INDICE v1.0
# Escanea capa caliente y escribe memoria\indice.json
# ============================================================

function Update-Indice {
    param (
        [string]$RutaBase
    )

    $rutaSalida = Join-Path $RutaBase "memoria\indice.json"

    # --- DISCOS ---
    $discos = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' } | ForEach-Object {
        [PSCustomObject]@{
            letra    = $_.Root
            etiqueta = if ($_.Description) { $_.Description } else { "" }
            libre_gb = [math]::Round($_.Free / 1GB, 2)
            total_gb = [math]::Round(($_.Used + $_.Free) / 1GB, 2)
        }
    }

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

    # --- CONSTRUIR OBJETO ---
    $indice = [PSCustomObject]@{
        generado         = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        discos           = $discos
        carpetas_usuario = $carpetasUsuario
        apps_instaladas  = $apps
    }

    # --- GUARDAR JSON (UTF-8 sin BOM) ---
    $json = $indice | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($rutaSalida, $json, [System.Text.UTF8Encoding]::new($false))

    Write-Host "[INDICE] indice.json actualizado." -ForegroundColor Cyan
}

Export-ModuleMember -Function Update-Indice
