import sys
import os
import argparse
import ctypes
import json
import re
import subprocess
import yaml
from datetime import datetime
from interpreter import interpreter

LOG_PROACTIVO = r"C:\JARVIS2\logs\proactivo.log"
os.makedirs(os.path.dirname(LOG_PROACTIVO), exist_ok=True)

def log(content):
    with open(LOG_PROACTIVO, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {content}\n")

def main():
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

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Ejecución proactiva (segundo plano) de JARVIS2")
    parser.add_argument("tarea", type=str, help="La orden a ejecutar")
    args = parser.parse_args()

    tarea = args.tarea
    log(f"[INICIO RUTINA] -> {tarea}")

    # Cargar configuracion base
    try:
        system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
        interpreter.system_message = system_msg + "\n\nESTAS EJECUTANDOTE EN SEGUNDO PLANO (MODO PROACTIVO). NO HABLES CON EL USUARIO, NO HAGAS PREGUNTAS. SIMPLEMENTE HAZ LA TAREA, GUARDA EL RESULTADO DONDE SE INDIQUE Y CIÉRRATE."
    except Exception as e:
        log(f"[ERROR] No se pudo leer system.md: {e}")
        sys.exit(1)

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

    interpreter.llm.context_window = 4096
    interpreter.llm.max_tokens = 2048
    interpreter.auto_run = True # Siempre auto en segundo plano
    
    # --- RAG: HIPOCAMPO / MEMORIA VECTORIAL ---
    prompt_final = tarea
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        chroma_client = chromadb.PersistentClient(path=r"C:\JARVIS2\vector_db")
        ollama_ef = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings", 
            model_name="nomic-embed-text"
        )
        collection = chroma_client.get_collection(name="jarvis_memory", embedding_function=ollama_ef)
        resultados = collection.query(query_texts=[tarea], n_results=2)
        
        if resultados and resultados.get('documents') and resultados['documents'][0]:
            fragmentos = "\n---\n".join(resultados['documents'][0])
            prompt_final = f"{tarea}\n\n[MEMORIA A LARGO PLAZO: He encontrado esto en mis archivos. Úsalo solo si es útil para responder:]\n{fragmentos}"
            log("[JARVIS-MEMORIA] Contexto inyectado en background.")
    except Exception:
        pass

    # Ejecutar la orden y recoger la respuesta
    try:
        modelo_elegido = seleccionar_cerebro(tarea)
        interpreter.llm.model = modelo_elegido
        log(f"[ROUTER MoE] Enrutando al cerebro especializado: {modelo_elegido}")

        response_text = ""
        for chunk in interpreter.chat(prompt_final, stream=True, display=False):
            if isinstance(chunk, dict) and chunk.get("type") == "message":
                response_text += chunk.get("content", "")
        
        log(f"[RESULTADO BRUTO] -> {response_text}")

        # --- PARCHE DE AUTOCURACIÓN PARA MODELOS LOCALES ---
        # Si el modelo ha vomitado un JSON de "execute" porque OpenInterpreter 
        # no lo ha procesado como código, lo capturamos y lo forzamos.
        if '"name": "execute"' in response_text and '"code":' in response_text:
            try:
                # Extraemos el bloque JSON (puede tener \n)
                # Buscamos el inicio { y el final } asumiendo que contiene "execute"
                inicio = response_text.find('{')
                fin = response_text.rfind('}')
                if inicio != -1 and fin != -1:
                    json_str = response_text[inicio:fin+1]
                    datos = json.loads(json_str)
                    
                    if datos.get("name") == "execute":
                        lang = datos["arguments"]["language"]
                        code = datos["arguments"]["code"]
                        
                        # Limpiamos los backticks de Markdown por si acaso
                        code = re.sub(r'```[a-zA-Z]*\n', '', code)
                        code = code.replace('```', '').strip()
                        
                        log(f"[AUTO-EJECUCIÓN FORZADA] Disparando {lang}...")
                        
                        if lang in ["powershell", "shell"]:
                            subprocess.run(["powershell", "-Command", code])
                        elif lang == "python":
                            subprocess.run(["python", "-c", code])
                        
                        log("[AUTO-EJECUCIÓN] Completada.")
            except Exception as ex:
                log(f"[ERROR AUTO-EJECUCIÓN] Falló el parche: {ex}")
    except Exception as e:
        log(f"[CRITICAL ERROR] Fallo durante la ejecución proactiva: {e}")
        if os.name == 'nt':
            msg = f"Fallo en rutina de fondo (proactivo.py).\nTarea: {tarea}\nDetalle: {e}"
            ctypes.windll.user32.MessageBoxW(0, msg, "Error de JARVIS en 2º plano", 0x10)

    log("[FIN RUTINA] Proceso cerrado correctamente.\n" + "-"*50)

if __name__ == "__main__":
    main()
