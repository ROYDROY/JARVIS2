Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3
& "C:\JARVIS2\venv\Scripts\Activate.ps1"
python "C:\JARVIS2\launcher.py"

# --- LIMPIEZA CATEGORIA A (al cierre de sesion) ---
Write-Host "`n[Limpieza] Eliminando temporales..." -ForegroundColor Gray
Get-ChildItem "C:\JARVIS2" -Recurse -Include "*.tmp","*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem "C:\JARVIS2" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "    OK" -ForegroundColor Gray
