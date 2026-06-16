import sys
import io
import os
import json
import re
import subprocess
import yaml
import traceback
from datetime import datetime
import threading
import queue
import time
import msvcrt

# Importar motor de voz
sys.path.append(r"C:\JARVIS2\herramientas")
try:
    from MotorVoz import hablar, escuchar, escuchar_pasivo
except Exception as e:
    def hablar(txt): pass
    def escuchar(): return ""
    def escuchar_pasivo(): return False
    
try:
    from NervioOptico import extraer_ruta_imagen, analizar_imagen_con_llava
except Exception as e:
    def extraer_ruta_imagen(txt): return None
    def analizar_imagen_con_llava(ruta): return None

# ==============================================================================
# ==============================================================================
# FIRMA ELECTRÓNICA Y LICENCIA DE USO
# SISTEMA: JARVIS 3.1 (MoE Local + Memoria RAG)
# PROPIEDAD INTELECTUAL DE: RUBÉN DÍAZ IGLESIAS
# CONTACTO COMERCIAL: RDIAZI@YAHOO.ES | Tlf: 616624850
# Queda terminantemente prohibida la copia, distribución o comercialización
# de esta arquitectura de Inteligencia Artificial sin el consentimiento
# expreso y directo del autor (asociado a su firma electrónica).
# ==============================================================================
# ==============================================================================

# Fijar codificación UTF-8 sin romper la consola nativa de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import colorama
colorama.just_fix_windows_console()

import builtins
try:
    from prompt_toolkit import prompt as pt_prompt
    def custom_input(prompt_text=""):
        val = pt_prompt(prompt_text)
        if val.strip().lower() in ("salir", "exit", "quit"):
            sys.exit(0)
        return val
except ImportError:
    _original_input = builtins.input
    def custom_input(prompt_text=""):
        val = _original_input(prompt_text)
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
interpreter.llm.context_window = 4096
interpreter.llm.max_tokens = 2048
interpreter.auto_run = True

CONFIG_PATH = r"C:\JARVIS2\config.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        config_data = yaml.safe_load(f)
        MODEL_CODER = config_data.get("model_coder", "ollama/qwen2.5-coder:14b")
        MODEL_CHAT = config_data.get("model_chat", "ollama/llama3.1:8b")
except Exception:
    MODEL_CODER = "ollama/qwen2.5-coder:14b"
    MODEL_CHAT = "ollama/llama3.1:8b"

def seleccionar_cerebro(prompt):
    prompt_lower = prompt.lower()
    keywords_codigo = ["script", "código", "codigo", "programa", "error", "fall", "powershell", "python", "automatiza", "archivo", "carpeta", "ejecut", "comando", "json", "terminal", "consola", "instala", "descarga"]
    if any(k in prompt_lower for k in keywords_codigo):
        return MODEL_CODER
    return MODEL_CHAT

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
            if s.get("hechos"):
                texto += f"  Hechos: {' | '.join(s['hechos'])}\n"
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
        tipo = indice.get("tipo_actualizacion", "Completa")
        texto_indice = f"Estado actual del sistema (generado: {indice.get('generado', '?')} - Actualizacion: {tipo}):\n"

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

print("\n" + "="*60)
print(" 🤖 SISTEMA JARVIS 3.1 (DOBLE CEREBRO MoE) INICIADO")
print(" 🔒 LICENCIA PRIVADA - PROPIEDAD DE RUBÉN DÍAZ IGLESIAS")
print(" 📧 Contacto: RDIAZI@YAHOO.ES | 📱 616624850")
print(" ⚠️ Prohibida su copia o uso comercial sin autorización.")
print("="*60 + "\n")
print(f"[{datetime.now().strftime('%H:%M:%S')}] JARVIS operativo. Escribe tu consulta.")
print("Comandos: 'salir' para cerrar | 'modo auto' para auto-aprobar | 'modo manual' para aprobar manualmente")

command_queue = queue.Queue()

def hilo_wake_word():
    """Hilo pasivo: Solo escucha la palabra mágica"""
    while True:
        if escuchar_pasivo():
            hablar("¿Sí, Rubén?")
            print("\n[WAKE WORD] Jarvis ha despertado. Escuchando comando...")
            cmd = escuchar()
            if cmd:
                command_queue.put(cmd)

# Lanzar el hilo del oído biónico
t = threading.Thread(target=hilo_wake_word, daemon=True)
t.start()

def get_input_async():
    """Entrada híbrida (Teclado + Voz en background)"""
    sys.stdout.write("> ")
    sys.stdout.flush()
    texto = ""
    while True:
        if not command_queue.empty():
            sys.stdout.write("\r> [Comando de Voz Recibido]\n")
            return command_queue.get()
            
        if msvcrt.kbhit():
            char = msvcrt.getwche()
            if char in ('\r', '\n'):
                sys.stdout.write("\n")
                return texto
            elif char == '\x08': # backspace
                texto = texto[:-1]
                sys.stdout.write(" \x08")
            elif char == '\x03': # ctrl+c
                raise KeyboardInterrupt
            else:
                texto += char
        time.sleep(0.05)

while True:
    try:
        user_input = get_input_async()
        if not user_input.strip():
            continue
    except (EOFError, KeyboardInterrupt):
        break

    cmd = user_input.strip().lower()

    if cmd in ("salir", "exit", "quit", "apagar"):
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
    try:
        # --- NERVIO ÓPTICO: DETECCIÓN DE IMÁGENES ---
        ruta_img = extraer_ruta_imagen(user_input)
        if ruta_img:
            desc_visual = analizar_imagen_con_llava(ruta_img)
            if desc_visual:
                # Limpiamos la ruta del input original para que no ensucie
                user_input_limpio = user_input.replace(ruta_img, "").replace('""', '').strip()
                if not user_input_limpio:
                    user_input_limpio = "Por favor, analiza la imagen que te he pasado y dime qué ves o ayúdame con lo que aparece en ella."
                    
                user_input = f"[SISTEMA VISUAL: El usuario ha proporcionado una imagen. Tu nervio óptico (Llava) la ha analizado y reporta lo siguiente:\n{desc_visual}]\n\nConsulta del usuario: {user_input_limpio}"
                
        # --- RAG: HIPOCAMPO / MEMORIA VECTORIAL ---
        prompt_final = user_input
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            chroma_client = chromadb.PersistentClient(path=r"C:\JARVIS2\vector_db")
            ollama_ef = embedding_functions.OllamaEmbeddingFunction(
                url="http://localhost:11434/api/embeddings", 
                model_name="nomic-embed-text"
            )
            collection = chroma_client.get_collection(name="jarvis_memory", embedding_function=ollama_ef)
            resultados = collection.query(query_texts=[user_input], n_results=2)
            
            if resultados and resultados.get('documents') and resultados['documents'][0]:
                fragmentos = "\n---\n".join(resultados['documents'][0])
                prompt_final = f"{user_input}\n\n[MEMORIA A LARGO PLAZO: He encontrado esto en mis archivos. Úsalo solo si es útil para responder:]\n{fragmentos}"
                print("\n[JARVIS-MEMORIA] He encontrado recuerdos sobre esto. Inyectando...")
        except Exception:
            pass

        modelo_elegido = seleccionar_cerebro(user_input)
        interpreter.llm.model = modelo_elegido
        
        # Llama 3.1 a veces falla si se le fuerza a usar funciones (devuelve {}). Se lo desactivamos.
        if "llama" in modelo_elegido.lower():
            interpreter.llm.supports_functions = False
        else:
            interpreter.llm.supports_functions = True
            
        print(f"\n[ROUTER MoE] Enrutando al cerebro especializado: {modelo_elegido}")

        for chunk in interpreter.chat(prompt_final, stream=True, display=True):
            if isinstance(chunk, dict) and chunk.get("type") == "message":
                response_text += chunk.get("content", "")
                
        # --- PARCHE DE AUTOCURACIÓN JSON ---
        if '"name": "execute"' in response_text and '"code":' in response_text:
            try:
                inicio = response_text.find('{')
                fin = response_text.rfind('}')
                if inicio != -1 and fin != -1:
                    json_str = response_text[inicio:fin+1]
                    datos = json.loads(json_str)
                    if datos.get("name") == "execute":
                        lang = datos["arguments"]["language"]
                        code = datos["arguments"]["code"]
                        code = re.sub(r'```[a-zA-Z]*\n', '', code)
                        code = code.replace('```', '').strip()
                        print(f"\n[AUTO-EJECUCIÓN FORZADA] {lang}...")
                        if lang in ["powershell", "shell"]:
                            subprocess.run(["powershell", "-Command", code])
                        elif lang == "python":
                            subprocess.run(["python", "-c", code])
            except Exception:
                pass
                
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] JARVIS no ha podido conectar con Ollama. Detalles: {e}")
        
    if response_text:
        log("jarvis", response_text)
        # JARVIS HABLA
        try:
            hablar(response_text)
        except:
            pass




