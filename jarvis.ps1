& "$PSScriptRoot\venv\Scripts\Activate.ps1"
interpreter --system_message (Get-Content "$PSScriptRoot\system.md" -Raw) --model ollama/qwen2.5:7b-instruct-q5_K_M