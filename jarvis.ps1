$root        = "C:\JARVIS2"
$logPath     = "$root\logs\sesion_actual.log"
$memoriaPath = "$root\memoria\memoria.json"
$systemPath  = "$root\system.md"

# ----- MODULOS -----
Import-Module "$root\modulos\indice.psm1" -Force

# ----- ARRANQUE OLLAMA PRIMERO -----
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

# ----- FORZAR CONSOLA UTF-8 -----
chcp 65001 | Out-Null

# ----- PROCESAR SESION ANTERIOR -----
if (Test-Path $logPath) {
    Write-Host "[Memoria] Procesando sesion anterior..." -ForegroundColor Gray
    $logContent = Get-Content $logPath -Raw -Encoding UTF8
    $prompt = "Resume esta sesion en JSON con exactamente estos campos: fecha (string con fecha actual en formato YYYY-MM-DD), temas (array de strings), decisiones (array de strings), archivos_modificados (array de strings). Devuelve UNICAMENTE el JSON, sin explicaciones, sin markdown, sin bloques de codigo. Sesion: $logContent"
    $body = @{ model = "qwen2.5:7b-instruct-q5_K_M"; prompt = $prompt; stream = $false } | ConvertTo-Json -Depth 3
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $body -ContentType "application/json"
        $resumenRaw = $response.response.Trim()
        if ($resumenRaw -match '(?s)(\{.*\})') {
            $resumenRaw = $matches[1]
        }
        $resumen = $resumenRaw | ConvertFrom-Json
        $tieneContenido = ($resumen.temas.Count -gt 0) -or ($resumen.decisiones.Count -gt 0) -or ($resumen.archivos_modificados.Count -gt 0)
        if ($tieneContenido) {
            $memoria = Get-Content $memoriaPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $memoria.sesiones += $resumen
            $memoria | ConvertTo-Json -Depth 10 | Set-Content $memoriaPath -Encoding UTF8
            Write-Host "  OK — sesion registrada" -ForegroundColor Gray
        } else {
            Write-Host "  AVISO — sesion sin contenido util, no registrada" -ForegroundColor Yellow
        }
        Remove-Item $logPath -Force
    } catch {
        Write-Host "  AVISO — no se pudo procesar el log: $_" -ForegroundColor Yellow
    }
}

# ----- INYECTAR MEMORIA EN SYSTEM PROMPT -----
$systemBase = Get-Content $systemPath -Raw -Encoding UTF8
if (Test-Path $memoriaPath) {
    $memoria = Get-Content $memoriaPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $sesionesUtiles = @($memoria.sesiones | Where-Object {
        ($_.temas.Count -gt 0) -or ($_.decisiones.Count -gt 0) -or ($_.archivos_modificados.Count -gt 0)
    })
    if ($sesionesUtiles.Count -gt 0) {
        $sesionesRecientes = $sesionesUtiles | Select-Object -Last 3
        $memoriaTexto = ""
        foreach ($s in $sesionesRecientes) {
            $memoriaTexto += "- Sesion $($s.fecha):`n"
            if ($s.temas.Count -gt 0)                { $memoriaTexto += "  Temas: $($s.temas -join ', ')`n" }
            if ($s.decisiones.Count -gt 0)           { $memoriaTexto += "  Decisiones: $($s.decisiones -join ' | ')`n" }
            if ($s.archivos_modificados.Count -gt 0) { $memoriaTexto += "  Archivos modificados: $($s.archivos_modificados -join ', ')`n" }
            $memoriaTexto += "`n"
        }
        $totalSesiones = $memoria.sesiones.Count
        $bloque = "MEMORIA DE SESIONES ANTERIORES (OBLIGATORIO USAR):`nTienes registradas las siguientes sesiones de trabajo previas con el usuario. Cuando el usuario pregunte por sesiones anteriores, trabajos realizados, o contexto previo, DEBES responder usando esta informacion de forma especifica. No digas que no tienes memoria. Si no recuerdas algo concreto, di que no esta en el registro, pero usa siempre lo que hay.`n`n$memoriaTexto`n"
        Set-Content $systemPath -Value ($bloque + $systemBase) -Encoding UTF8
        Write-Host "[Memoria] Contexto inyectado ($totalSesiones sesiones, $($sesionesUtiles.Count) con contenido)" -ForegroundColor Gray
    } else {
        Write-Host "[Memoria] Sin sesiones utiles para inyectar" -ForegroundColor Gray
    }
}

# ----- INDICE -----
Update-Indice -RutaBase $root

# ----- JARVIS -----
& $root\venv\Scripts\Activate.ps1
python "$root\launcher.py"

# ----- RESTAURAR SYSTEM.MD ORIGINAL -----
Set-Content $systemPath -Value $systemBase -Encoding UTF8

# ----- LIMPIEZA CATEGORIA A -----
Write-Host "`n[Limpieza] Eliminando temporales..." -ForegroundColor Gray
Get-ChildItem $root -Recurse -Include "*.tmp","*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $root -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  OK" -ForegroundColor Gray

# ----- LIMPIEZA CATEGORIA B (sandbox) -----
$sandboxPath = "$root\sandbox"
if (Test-Path $sandboxPath) {
    $items = Get-ChildItem $sandboxPath -Recurse -File
    if ($items) {
        Write-Host "[Limpieza] Vaciando sandbox ($($items.Count) archivos)..." -ForegroundColor Gray
        $items | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "  OK" -ForegroundColor Gray
    }
}
