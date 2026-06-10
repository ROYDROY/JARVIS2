$root        = "C:\JARVIS2"
$logPath     = "$root\logs\sesion_actual.log"
$memoriaPath = "$root\memoria\memoria.json"
$systemPath  = "$root\system.md"

# ----- CARGADOR DE MODULOS (DIAGNOSTICO) -----
Write-Host "\n[Diagnostico de Arranque] Iniciando modulos..." -ForegroundColor Cyan
& $root\venv\Scripts\Activate.ps1
$activeModulesJson = python -c "import json, yaml; config=yaml.safe_load(open(r'$root\config.yaml', encoding='utf-8')); active=[m['ruta'] for k,m in config.get('modulos',{}).items() if m.get('estado')=='activo' and m.get('ruta','').endswith('.psm1')]; print(json.dumps(active))"
$activeModules = $activeModulesJson | ConvertFrom-Json

foreach ($mod in $activeModules) {
    $modPath = "$root\$mod"
    if (Test-Path $modPath) {
        try {
            Import-Module $modPath -Force -ErrorAction Stop
            $meta = Get-Variable "ModuloMetadata" -ValueOnly -ErrorAction SilentlyContinue
            if ($meta) {
                Write-Host "  [+] Modulo [$($meta.Nombre) v$($meta.Version)] - OK" -ForegroundColor Green
            } else {
                Write-Host "  [?] Modulo [$(Split-Path $modPath -Leaf)] - OK (Sin metadatos)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  [-] Modulo [$(Split-Path $modPath -Leaf)] - ERROR AISLADO: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  [-] Modulo no encontrado: $modPath" -ForegroundColor Red
    }
}
Write-Host "----------------------------------------\n" -ForegroundColor Cyan


# ----- ARRANQUE OLLAMA PRIMERO -----
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

# ----- FORZAR CONSOLA UTF-8 -----
chcp 65001 | Out-Null

# ----- PROCESAR SESION ANTERIOR -----
python "$root\procesar_sesion.py"


# ----- JARVIS -----
& $root\venv\Scripts\Activate.ps1
python "$root\launcher.py"

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





