Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

$root        = "C:\JARVIS2"
$logPath     = "$root\logs\sesion_actual.log"
$memoriaPath = "$root\memoria\memoria.json"
$systemPath  = "$root\system.md"

# --- PROCESAR SESION ANTERIOR ---
if (Test-Path $logPath) {
    Write-Host "[Memoria] Procesando sesion anterior..." -ForegroundColor Gray
    $logContent = Get-Content $logPath -Raw -Encoding UTF8
    $prompt = "Eres un asistente que genera resumenes estructurados. Resume la siguiente sesion de trabajo en formato JSON con esta estructura exacta: {"fecha":"FECHA","temas":[],"decisiones":[],"archivos_modificados":[]}. Solo devuelve el JSON, sin explicaciones ni texto adicional. Sesion:
$logContent"
    $body = @{ model = "qwen2.5:7b-instruct-q5_K_M"; prompt = $prompt; stream = $false } | ConvertTo-Json -Depth 3
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $body -ContentType "application/json"
        $resumenRaw = $response.response.Trim()
        $resumenRaw = $resumenRaw -replace '^`json','' -replace '^`','' -replace '`$','' 
        $resumen = $resumenRaw | ConvertFrom-Json
        $memoria = Get-Content $memoriaPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $memoria.sesiones += $resumen
        $memoria | ConvertTo-Json -Depth 10 | Set-Content $memoriaPath -Encoding UTF8
        Remove-Item $logPath -Force
        Write-Host "    OK -- sesion registrada" -ForegroundColor Gray
    } catch {
        Write-Host "    AVISO -- no se pudo procesar el log: $_" -ForegroundColor Yellow
    }
}

# --- INYECTAR MEMORIA EN SYSTEM PROMPT ---
$systemBase = Get-Content $systemPath -Raw -Encoding UTF8
if (Test-Path $memoriaPath) {
    $memoria = Get-Content $memoriaPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($memoria.sesiones.Count -gt 0 -or $memoria.hechos.Count -gt 0) {
        $memoriaTexto = $memoria | ConvertTo-Json -Depth 10
        $bloque = "[MEMORIA]
$memoriaTexto
[/MEMORIA]

"
        Set-Content $systemPath -Value ($bloque + $systemBase) -Encoding UTF8
        Write-Host "[Memoria] Contexto inyectado ($($memoria.sesiones.Count) sesiones, $($memoria.hechos.Count) hechos)" -ForegroundColor Gray
    }
}

# --- ARRANQUE NORMAL ---
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3
& "$root\venv\Scripts\Activate.ps1"
python "$root\launcher.py"

# --- RESTAURAR SYSTEM.MD ORIGINAL ---
Set-Content $systemPath -Value $systemBase -Encoding UTF8

# --- LIMPIEZA CATEGORIA A ---
Write-Host "`n[Limpieza] Eliminando temporales..." -ForegroundColor Gray
Get-ChildItem $root -Recurse -Include "*.tmp","*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $root -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "    OK" -ForegroundColor Gray
