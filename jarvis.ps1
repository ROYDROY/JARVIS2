Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3
& "C:\JARVIS2\venv\Scripts\Activate.ps1"
python "C:\JARVIS2\launcher.py"
