import sys
import io
import os
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from interpreter import interpreter

LOG_PATH = r"C:\JARVIS2\logs\sesion_actual.log"
os.makedirs(r"C:\JARVIS2\logs", exist_ok=True)

system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8").read()
interpreter.system_message = system_msg
interpreter.llm.model = "ollama/qwen2.5:7b-instruct-q5_K_M"
interpreter.llm.context_window = 8192
interpreter.llm.max_tokens = 2048
interpreter.auto_run = False

def log(role, content):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {role.upper()}: {content}\n")

print("JARVIS2 operativo. Escribe tu consulta.")
print("Comandos: 'salir' para cerrar | 'modo auto' para auto-aprobar | 'modo manual' para aprobar manualmente")

while True:
    try:
        user_input = input("> ")
    except (EOFError, KeyboardInterrupt):
        break

    cmd = user_input.strip().lower()

    if cmd in ("salir", "exit", "quit"):
        break
    elif cmd == "modo auto":
        interpreter.auto_run = True
        print("[MODO AUTO] Ejecucion automatica activada.")
        log("sistema", "modo auto activado")
        continue
    elif cmd == "modo manual":
        interpreter.auto_run = False
        print("[MODO MANUAL] Aprobacion manual activada.")
        log("sistema", "modo manual activado")
        continue

    log("usuario", user_input)
    response_text = ""
    for chunk in interpreter.chat(user_input, stream=True, display=True):
        if isinstance(chunk, dict) and chunk.get("type") == "message":
            response_text += chunk.get("content", "")
    if response_text:
        log("jarvis", response_text)
