ps1_path = r"C:\JARVIS2\jarvis.ps1"

with open(ps1_path, 'r', encoding='utf-8') as f:
    content = f.read()

loader_code = """# ----- CARGADOR DE MODULOS (DIAGNOSTICO) -----
Write-Host "\\n[Diagnostico de Arranque] Iniciando modulos..." -ForegroundColor Cyan
& $root\\venv\\Scripts\\Activate.ps1
$activeModulesJson = python -c "import json, yaml; config=yaml.safe_load(open(r'$root\\config.yaml', encoding='utf-8')); active=[m['ruta'] for k,m in config.get('modulos',{}).items() if m.get('estado')=='activo' and m.get('ruta','').endswith('.psm1')]; print(json.dumps(active))"
$activeModules = $activeModulesJson | ConvertFrom-Json

foreach ($mod in $activeModules) {
    $modPath = "$root\\$mod"
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
Write-Host "----------------------------------------\\n" -ForegroundColor Cyan
"""

import re
# Regex to match the whole block to replace
pattern1 = re.compile(r"# ----- MODULOS -----.*?Import-Module \"\$root\\modulos\\indice\.psm1\" -Force", re.DOTALL)
content = pattern1.sub(lambda m: loader_code, content)

pattern2 = re.compile(r"# ----- INDICE -----.*?Update-Indice -RutaBase \$root\n", re.DOTALL)
content = pattern2.sub(lambda m: "", content)

with open(ps1_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modulos actualizados en jarvis.ps1")
