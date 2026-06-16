import os
import sys
import threading
import queue
import time
import json
import re
import yaml
import subprocess
import speech_recognition as sr
import customtkinter as ctk
from dotenv import load_dotenv

# Cargar credenciales al arrancar
load_dotenv(r"C:\JARVIS2\.env")

# ==============================================================================
# IMPORTACIONES JARVIS
# ==============================================================================
from interpreter import interpreter

sys.path.append(r"C:\JARVIS2\herramientas")
try:
    from MotorVoz import hablar, escuchar, escuchar_pasivo
except Exception:
    def hablar(txt): pass
    def escuchar(device_index=None): return ""
    def escuchar_pasivo(device_index=None): return False

# Variable global para saber si Jarvis está hablando físicamente
is_speaking_global = False

def hablar_y_esperar(texto):
    global is_speaking_global
    is_speaking_global = True
    try:
        hablar(texto)
    finally:
        is_speaking_global = False

try:
    from NervioOptico import extraer_ruta_imagen, analizar_imagen_con_llava
except Exception:
    def extraer_ruta_imagen(txt): return None
    def analizar_imagen_con_llava(ruta): return None

# ==============================================================================
# CONFIGURACION INTERPRETER Y OLLAMA
# ==============================================================================
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
    
    # 1. Gatillos Gemini (Cirujano Especialista)
    keywords_gemini = ["analiza", "resume", "largo", "imagen", "foto", "explica a fondo", "traduce", "experto", "complejo", "redacta"]
    if any(k in prompt_lower for k in keywords_gemini):
        return "gemini/gemini-1.5-pro-latest"
        
    # 2. Gatillos Qwen (Código y Sistema Local)
    keywords_codigo = ["script", "código", "codigo", "programa", "error", "fall", "powershell", "python", "automatiza", "archivo", "carpeta", "ejecut", "comando", "json", "terminal", "consola", "instala", "descarga"]
    if any(k in prompt_lower for k in keywords_codigo):
        return MODEL_CODER
        
    # 3. Defecto: Llama (Charla diaria ultra-rápida y privada)
    return MODEL_CHAT

# ==============================================================================
# CLASE PRINCIPAL GUI
# ==============================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JARVIS 4.0 - Interfaz Unificada")
        self.geometry("1100x700")
        self.minsize(800, 600)

        # Configurar grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Colas para hilos
        self.ui_queue = queue.Queue()
        self.is_generating = False

        # Cargar micros y arreglar codificación (MicrÃ³fono -> Micrófono)
        raw_mics = sr.Microphone.list_microphone_names()
        self.mics = ["Predeterminado de Windows"]
        for m in raw_mics:
            try:
                self.mics.append(m.encode('latin1').decode('utf-8'))
            except:
                self.mics.append(m)
                
        idx_guardado = config_data.get("mic_index", 0) if "config_data" in globals() and config_data else 0
        if idx_guardado >= len(self.mics): idx_guardado = 0
        self.selected_mic_index = idx_guardado

        self.construir_ui()
        
        # Configurar interpreter
        system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
        interpreter.system_message = system_msg
        interpreter.llm.api_base = "http://localhost:11434"
        interpreter.llm.context_window = 4096
        interpreter.llm.max_tokens = 2048
        interpreter.auto_run = True
        interpreter.conversation_filename = "jarvis_unified_session.json"

        # Iniciar Wake Word en background
        self.hilo_ww = threading.Thread(target=self.hilo_wake_word, daemon=True)
        self.hilo_ww.start()

        # Bucle de actualización de UI
        self.after(100, self.procesar_cola)

    def construir_ui(self):
        # ==============================================================================
        # PANEL LATERAL (IZQUIERDA)
        # ==============================================================================
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🤖 JARVIS 4.0", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Sección: Control de Voz
        self.lbl_voz = ctk.CTkLabel(self.sidebar_frame, text="🎙️ Control de Voz", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_voz.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Combo Micros
        self.combo_mic = ctk.CTkComboBox(self.sidebar_frame, values=self.mics, command=self.cambiar_mic)
        self.combo_mic.set(self.mics[self.selected_mic_index] if self.mics else "Ninguno")
        self.combo_mic.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.switch_escucha_var = ctk.BooleanVar(value=True)
        self.switch_escucha = ctk.CTkSwitch(self.sidebar_frame, text="Escucha Activa", variable=self.switch_escucha_var)
        self.switch_escucha.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.btn_hablar = ctk.CTkButton(self.sidebar_frame, text="🎤 Hablar ahora", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.hablar_boton)
        self.btn_hablar.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Sección: Expansiones
        self.lbl_exp = ctk.CTkLabel(self.sidebar_frame, text="🧩 Expansiones", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_exp.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        self.switch_memoria = ctk.CTkSwitch(self.sidebar_frame, text="Memoria Vectorial")
        self.switch_memoria.grid(row=7, column=0, padx=20, pady=10, sticky="w")
        self.switch_memoria.select() # Activo por defecto

        self.switch_youtube = ctk.CTkSwitch(self.sidebar_frame, text="YouTube")
        self.switch_youtube.grid(row=8, column=0, padx=20, pady=10, sticky="w")
        self.switch_youtube.select()

        # Apagar
        self.btn_apagar = ctk.CTkButton(self.sidebar_frame, text="🛑 Apagar", fg_color="#8B0000", hover_color="#5C0000", command=self.destroy)
        self.btn_apagar.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # ==============================================================================
        # PANEL CENTRAL (CHAT)
        # ==============================================================================
        self.chat_frame = ctk.CTkFrame(self, corner_radius=10)
        self.chat_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self.chat_frame, wrap="word", font=ctk.CTkFont(size=14))
        self.textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.textbox.insert("0.0", "Bienvenido a JARVIS 4.0. Sistemas en línea.\n\n")
        self.textbox.configure(state="disabled")

        # ==============================================================================
        # BARRA INFERIOR (INPUT)
        # ==============================================================================
        self.input_frame = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=(20, 20), pady=(10, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry_comando = ctk.CTkEntry(self.input_frame, placeholder_text="Pídele algo a JARVIS...", height=40, font=ctk.CTkFont(size=14))
        self.entry_comando.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.entry_comando.bind("<Return>", self.enviar_mensaje)

        self.btn_enviar = ctk.CTkButton(self.input_frame, text="Enviar ➔", width=100, height=40, command=self.enviar_mensaje)
        self.btn_enviar.grid(row=0, column=1, padx=0, pady=0)

    def cambiar_mic(self, choice):
        self.selected_mic_index = self.mics.index(choice)
        if "config_data" in globals():
            config_data["mic_index"] = self.selected_mic_index
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            except: pass

    def hablar_boton(self):
        if self.is_generating: return
        self.ui_queue.put(("estado", "Escuchando..."))
        hablar_y_esperar("Te escucho")
        real_idx = self.get_real_mic_index()
        cmd = escuchar(device_index=real_idx)
        self.ui_queue.put(("estado", "Listo"))
        if cmd:
            self.ejecutar_prompt(cmd)

    def get_real_mic_index(self):
        """Convierte el índice de la UI al índice real de PyAudio"""
        if self.selected_mic_index == 0:
            return None # Predeterminado
        return self.selected_mic_index - 1 # Restamos 1 por la opción 'Predeterminado'

    def hilo_wake_word(self):
        global is_speaking_global
        while True:
            # Solo escucha si no está generando respuesta Y tampoco está hablando en voz alta
            if not self.is_generating and not is_speaking_global and self.switch_escucha_var.get():
                real_idx = self.get_real_mic_index()
                if escuchar_pasivo(device_index=real_idx):
                    self.ui_queue.put(("estado", "Escuchando WakeWord..."))
                    hablar_y_esperar("¿Sí, Rubén?")
                    cmd = escuchar(device_index=real_idx)
                    if cmd:
                        self.ejecutar_prompt(cmd)
            time.sleep(1)

    def enviar_mensaje(self, event=None):
        texto = self.entry_comando.get()
        if not texto.strip() or self.is_generating: return
        self.entry_comando.delete(0, "end")
        self.ejecutar_prompt(texto)

    def ejecutar_prompt(self, texto):
        self.is_generating = True
        self.escribir_chat(f"\n[Tú]: {texto}\n")
        self.ui_queue.put(("estado", "Pensando..."))
        
        threading.Thread(target=self.generar_respuesta_llm, args=(texto,), daemon=True).start()

    def generar_respuesta_llm(self, prompt):
        try:
            prompt_final = prompt
            
            # --- RAG: MEMORIA VECTORIAL ---
            if self.switch_memoria.get():
                try:
                    import chromadb
                    from chromadb.utils import embedding_functions
                    chroma_client = chromadb.PersistentClient(path=r"C:\JARVIS2\vector_db")
                    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
                        url="http://localhost:11434/api/embeddings", 
                        model_name="nomic-embed-text"
                    )
                    collection = chroma_client.get_collection(name="jarvis_memory", embedding_function=ollama_ef)
                    resultados = collection.query(query_texts=[prompt], n_results=2)
                    if resultados and resultados.get('documents') and resultados['documents'][0]:
                        fragmentos = "\n---\n".join(resultados['documents'][0])
                        prompt_final = f"{prompt}\n\n[MEMORIA A LARGO PLAZO:]\n{fragmentos}"
                        self.ui_queue.put(("chat", "\n[JARVIS-MEMORIA] He encontrado recuerdos sobre esto...\n"))
                except Exception:
                    pass

            # --- BUSCADOR EN INTERNET (DUCKDUCKGO) ---
            prompt_lower = prompt.lower()
            keywords_busqueda = ["busca", "internet", "quien es", "quién es", "qué es", "que es", "noticias", "actualidad", "últimas", "último", "hoy", "precio", "tiempo hace"]
            if any(k in prompt_lower for k in keywords_busqueda):
                try:
                    from Buscador import buscar_en_internet
                    self.ui_queue.put(("estado", "Buscando en la red..."))
                    self.ui_queue.put(("chat", "\n[JARVIS-RED] Consultando internet (DuckDuckGo)...\n"))
                    resultados_web = buscar_en_internet(prompt, max_resultados=3)
                    if "No he encontrado" not in resultados_web and "Todos los resultados" not in resultados_web:
                        prompt_final = f"{prompt_final}\n\n[RESULTADOS ACTUALIZADOS DE INTERNET (IGNORANDO WIKIPEDIA):]\n{resultados_web}\n\nPor favor, usa obligatoriamente esta información para responder al usuario de forma natural, sin mencionar los enlaces enteros a no ser que te lo pida."
                except Exception as e:
                    self.ui_queue.put(("chat", f"\n[ERROR BUSCADOR] {e}\n"))

            # --- SELECCIÓN CEREBRO MoE ---
            modelo_elegido = seleccionar_cerebro(prompt)
            interpreter.llm.model = modelo_elegido
            
            # Cortafuegos dinámico (Abre puerta a internet solo si es Gemini)
            if "gemini" in modelo_elegido.lower():
                interpreter.llm.api_base = None
            else:
                interpreter.llm.api_base = "http://localhost:11434"
                
            if "llama" in modelo_elegido.lower():
                interpreter.llm.supports_functions = False
            else:
                interpreter.llm.supports_functions = True
            
            self.ui_queue.put(("chat", f"\n[MoE] Usando cerebro: {modelo_elegido}\n[JARVIS]: "))
            
            response_text = ""
            for chunk in interpreter.chat(prompt_final, stream=True, display=False):
                if isinstance(chunk, dict) and chunk.get("type") == "message":
                    content = chunk.get("content", "")
                    if content:
                        response_text += content
                        self.ui_queue.put(("chat_stream", content))
            
            self.ui_queue.put(("chat", "\n"))
            
            # Autoejecución parche JSON
            if '"name": "execute"' in response_text and '"code":' in response_text:
                self.ui_queue.put(("chat", "[Ejecutando código extraído...]\n"))
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
                            if lang in ["powershell", "shell"]:
                                subprocess.run(["powershell", "-Command", code])
                            elif lang == "python":
                                subprocess.run(["python", "-c", code])
                except Exception:
                    pass
                
            if response_text:
                self.ui_queue.put(("hablar", response_text))

        except Exception as e:
            self.ui_queue.put(("chat", f"\n[ERROR CRÍTICO] {e}\n"))
        finally:
            self.is_generating = False
            self.ui_queue.put(("estado", "Listo"))

    def escribir_chat(self, texto):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", texto)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def procesar_cola(self):
        while not self.ui_queue.empty():
            tipo, valor = self.ui_queue.get()
            if tipo == "chat":
                self.escribir_chat(valor)
            elif tipo == "chat_stream":
                self.textbox.configure(state="normal")
                self.textbox.insert("end", valor)
                self.textbox.configure(state="disabled")
                self.textbox.see("end")
            elif tipo == "hablar":
                # Lo lanzamos en un mini-hilo usando la función que marca is_speaking_global
                threading.Thread(target=hablar_y_esperar, args=(valor,), daemon=True).start()
            elif tipo == "estado":
                pass
        self.after(100, self.procesar_cola)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
