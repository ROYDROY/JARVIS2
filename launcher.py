import sys
import io
import os
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import builtins
_original_input = builtins.input

def custom_input(prompt=""):
    val = _original_input(prompt)
    if val.strip().lower() in ("salir", "exit", "quit"):
        sys.exit(0)
    return val

builtins.input = custom_input

from interpreter import interpreter

LOG_PATH     = r"C:\JARVIS2\logs\sesion_actual.log"
MEMORIA_PATH = r"C:\JARVIS2\memoria\memoria.json"
INDICE_PATH  = r"C:\JARVIS2\memoria\indice.json"
os.makedirs(r"C:\JARVIS2\logs", exist_ok=True)

system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
interpreter.system_message = system_msg
interpreter.llm.model = "ollama/qwen2.5:7b-instruct-q5_K_M"
interpreter.llm.context_window = 8192
interpreter.llm.max_tokens = 2048
interpreter.auto_run = False

# ----- INYECTAR MEMORIA COMO HISTORIAL DE CONVERSACION -----
if os.path.exists(MEMORIA_PATH):
    with open(MEMORIA_PATH, "r", encoding="utf-8-sig") as f:
        memoria = json.load(f)
    sesiones_utiles = [s for s in memoria.get("sesiones", [])
                       if s.get("temas") or s.get("decisiones") or s.get("archivos_modificados")]
    if sesiones_utiles:
        sesiones_recientes = sesiones_utiles[-3:]
        texto = "Sesiones de trabajo previas registradas en mi memoria:\n"
        for s in sesiones_recientes:
            texto += f"- Sesion {s.get('fecha', '?')}:\n"
            if s.get("temas"):
                texto += f"  Temas: {', '.join(s['temas'])}\n"
            if s.get("decisiones"):
                texto += f"  Decisiones: {' | '.join(s['decisiones'])}\n"
            if s.get("archivos_modificados"):
                texto += f"  Archivos modificados: {', '.join(s['archivos_modificados'])}\n"
        interpreter.messages = [
            {"role": "user",      "type": "message", "content": texto},
            {"role": "assistant", "type": "message", "content": "Memoria cargada. Tengo registro de esas sesiones y las usare como contexto durante esta sesion."}
        ]

# ----- INYECTAR INDICE DEL SISTEMA -----
if os.path.exists(INDICE_PATH):
    with open(INDICE_PATH, "r", encoding="utf-8-sig") as f:
        indice = json.load(f)
    if indice and indice != {}:
        texto_indice = f"Estado actual del sistema (generado: {indice.get('generado', '?')}):\n"

        discos = indice.get("discos", [])
        if discos:
            texto_indice += "Discos:\n"
            for d in discos:
                texto_indice += f"  - {d.get('letra')} {d.get('etiqueta','')} | Libre: {d.get('libre_gb')} GB / Total: {d.get('total_gb')} GB\n"

        carpetas = indice.get("carpetas_usuario", [])
        if carpetas:
            texto_indice += "Carpetas del usuario:\n"
            for c in carpetas:
                texto_indice += f"  - {c}\n"

        apps = indice.get("apps_instaladas", [])
        if apps:
            texto_indice += f"Aplicaciones instaladas ({len(apps)} en total): {', '.join(apps[:20])}"
            if len(apps) > 20:
                texto_indice += f" ... y {len(apps) - 20} mas."
            texto_indice += "\n"

        if not hasattr(interpreter, "messages") or interpreter.messages is None:
            interpreter.messages = []
        interpreter.messages += [
            {"role": "user",      "type": "message", "content": texto_indice},
            {"role": "assistant", "type": "message", "content": "Indice del sistema cargado. Conozco los discos, carpetas y aplicaciones disponibles."}
        ]
        print("[Indice] Contexto del sistema inyectado.")

def log(role, content):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{role.upper()}]: {content}\n")

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




