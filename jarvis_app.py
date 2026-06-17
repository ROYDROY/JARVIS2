import os
import sys
import threading
import queue
import time
import json
import re
import yaml
import subprocess
import requests
import speech_recognition as sr
import pyautogui
import keyboard
import customtkinter as ctk
import uuid
try:
    import windnd
except ImportError:
    windnd = None
from datetime import datetime
from dotenv import load_dotenv, set_key

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
config_data = {}
try:
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        config_data = yaml.safe_load(f) or {}
        MODEL_CODER = config_data.get("model_coder", "ollama/qwen2.5-coder:14b")
        MODEL_CHAT = config_data.get("model_chat", "ollama/llama3.1:8b")
except Exception:
    MODEL_CODER = "ollama/qwen2.5-coder:14b"
    MODEL_CHAT = "ollama/llama3.1:8b"

def seleccionar_cerebro(prompt, modo="Automático"):
    prompt_lower = prompt.lower()
    
    # Detectar APIs activas en el entorno
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    
    # Detectar si hay un archivo adjunto en el prompt
    tiene_archivo = "[Archivo:" in prompt
    tiene_imagen = False
    if tiene_archivo:
        # Detectar extensiones comunes de imagen en la ruta
        tiene_imagen = any(ext in prompt_lower for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"])
    
    # Identificar tarea en modo Automático
    es_codigo = False
    es_analisis = False
    es_autonomo = False  # NUEVO: tareas que requieren ejecución real + escritura de archivos
    
    if modo == "Automático":
        if tiene_imagen:
            es_analisis = True
        elif tiene_archivo:
            # Si tiene otro archivo no imagen, requiere ingeniería (leer pdf/excel/zip, etc.)
            es_codigo = True
        else:
            # Tareas autónomas pesadas: análisis del sistema, informes, auditorías
            keywords_autonomo = ["audita", "analiza el pc", "analiza el ordenador", "analiza mi pc", "analiza mi ordenador",
                                 "genera un informe", "crea un informe", "escribe un informe",
                                 "investiga el", "diagnóstico", "diagnostico", "examina el sistema",
                                 "revisa el sistema", "escanea", "escan", "escán", "scann", "scaner"]
            if any(k in prompt_lower for k in keywords_autonomo):
                es_autonomo = True
            else:
                keywords_codigo = ["script", "código", "codigo", "programa", "error", "fall",
                                   "powershell", "python", "automatiza", "archivo", "carpeta",
                                   "ejecut", "comando", "json", "terminal", "consola", "instala", 
                                   "descarga", "arranca", "abr", "inicia", "cierr", "apaga", "reinicia",
                                   "borr", "elimin", "quit", "suprim", "destruy", "carg", "mat"]
                if any(k in prompt_lower for k in keywords_codigo):
                    es_codigo = True
                else:
                    keywords_analisis = ["analiza", "resume", "largo", "imagen", "foto",
                                         "explica a fondo", "traduce", "experto", "complejo", "redacta"]
                    if any(k in prompt_lower for k in keywords_analisis):
                        es_analisis = True

    # === RANKING DINÁMICO POR ROLES ===
    
    if modo.startswith("Forzar: "):
        nombre_api = modo.replace("Forzar: ", "").strip()
        diccionario_modelos = {
            "NVIDIA": "nvidia_nim/meta/llama3-70b-instruct",
            "MISTRAL": "mistral/mistral-large-latest",
            "COHERE": "cohere/command-r-plus",
            "DEEPSEEK": "deepseek/deepseek-coder",
            "OPENROUTER": "openrouter/auto"
        }
        return diccionario_modelos.get(nombre_api, f"{nombre_api.lower()}/auto")
    
    # NIVEL 3 - Tareas autónomas complejas: Local potente primero, nube como red de seguridad
    if es_autonomo:
        return MODEL_CODER 
    
    if modo == "Ingeniero" or es_codigo:
        if has_openai: return "openai/gpt-4o"
        if has_anthropic: return "anthropic/claude-3-5-sonnet-20240620"
        return MODEL_CODER
        
    elif modo == "Análisis" or es_analisis:
        if has_gemini: return "gemini/gemini-2.5-flash"
        if has_anthropic: return "anthropic/claude-3-5-sonnet-20240620"
        if has_openai: return "openai/gpt-4o"
        return MODEL_CODER
        
    elif modo == "Conversación":
        # Evitar bypass de charla cuando hay archivos que procesar
        if not tiene_archivo and has_groq: return "groq/llama3-70b-8192"
        return MODEL_CHAT
        
    # Defecto: charla ligera local
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

        # Colas e inicialización
        self.ui_queue = queue.Queue()
        self.is_generating = False
        self._prompt_lock = threading.Lock()  # Evita ejecución concurrente de dos prompts
        self._admin_granted_event = threading.Event()  # Señal para detectar activación del Modo Admin
        self._abortar_generacion = False
        self._current_response_streamed = False

        # Cargar micros y arreglar codificación (nombre puede venir mal codificado)
        raw_mics = sr.Microphone.list_microphone_names()
        self.mics = ["Predeterminado de Windows"]
        for m in raw_mics:
            try:
                self.mics.append(m.encode('latin1').decode('utf-8'))
            except Exception:
                self.mics.append(m)
                
        idx_guardado = config_data.get("mic_index", 0) if config_data else 0
        if idx_guardado >= len(self.mics): idx_guardado = 0
        self.selected_mic_index = idx_guardado

        self.construir_ui()
        
        # Configurar interpreter
        try:
            with open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig") as _f:
                system_msg = _f.read()
        except FileNotFoundError:
            SYSTEM_CHAT = (
                "Eres JARVIS, el asistente personal de Rubén. "
                "Compórtate de forma muy natural, coloquial y directa. "
                "El usuario solo quiere charlar o hacer preguntas sencillas. "
                "CRÍTICO: TÚ ERES EL MODO CHARLA Y NO PUEDES EJECUTAR NADA. Si el usuario menciona programas, archivos o parece que quiere que operes el PC, "
                "NUNCA te inventes comandos ni finjas que estás abriendo/cerrando programas. DEBES responder: 'Dímelo usando palabras como Abrir, Cerrar o Ejecutar para activar mi núcleo de ingeniería'. "
                "Responde de forma conversacional y corta."
            )
            SYSTEM_LOCAL = (
                "Eres JARVIS, el sistema de ejecución de código. "
                "CRÍTICO: Escribe ÚNICAMENTE bloques de código. NO escribas texto explicativo antes ni después del bloque de código. "
                "NO narrar tus pensamientos, no digas 'Aquí tienes el código' ni 'He completado la tarea'. "
                "Responde solo con el bloque de código necesario."
            )
            system_msg = SYSTEM_CHAT + "\n" + SYSTEM_LOCAL
            self.ui_queue.put(("chat", "\n[AVISO] No se encontró system.md. Usando personalidad por defecto.\n"))
        interpreter.system_message = system_msg
        interpreter.llm.api_base = "http://localhost:11434"
        interpreter.llm.context_window = 4096
        interpreter.llm.max_tokens = 2048
        interpreter.auto_run = True
        interpreter.conversation_filename = "jarvis_unified_session.json"
        
        # Cargar memoria RAM a corto plazo (para no perder el hilo al reiniciar la app)
        try:
            if os.path.exists(r"C:\JARVIS2\ram_history.json"):
                with open(r"C:\JARVIS2\ram_history.json", "r", encoding="utf-8") as f:
                    interpreter.messages = json.load(f)
        except Exception:
            interpreter.messages = []

        # Iniciar Wake Word en background
        self.hilo_ww = threading.Thread(target=self.hilo_wake_word, daemon=True)
        self.hilo_ww.start()

        # Freno de Mano (Failsafe ESC)
        try:
            pyautogui.FAILSAFE = True
            keyboard.add_hotkey('esc', lambda: pyautogui.moveTo(0, 0))
        except Exception:
            pass

        # Drag & Drop Nativo (windnd)
        if windnd:
            try:
                windnd.hook_dropfiles(self, func=self.on_drop_files)
            except Exception:
                pass

        # Bucle de actualización de UI y Rutinas
        self.after(100, self.procesar_cola)
        self.after(2000, self.revisar_rutinas_arranque)

    def revisar_rutinas_arranque(self):
        try:
            ruta_rutinas = r"C:\JARVIS2\config\rutinas.json"
            if os.path.exists(ruta_rutinas):
                with open(ruta_rutinas, "r", encoding="utf-8") as f:
                    rutinas = json.load(f)
                if rutinas and isinstance(rutinas, list):
                    msg = "Sistemas en línea. Tareas programadas: " + ", ".join(rutinas)
                    self.ui_queue.put(("chat", f"\n[RUTINAS] {msg}\n"))
                    self.ui_queue.put(("hablar", msg))
        except Exception:
            pass

    def actualizar_modos_combobox(self):
        modos_base = ["Automático", "Conversación", "Análisis", "Ingeniero"]
        apis_base = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]
        
        for k in os.environ.keys():
            if k.endswith("_API_KEY") and k not in apis_base:
                nombre = k.replace("_API_KEY", "")
                modos_base.append(f"Forzar: {nombre}")
                
        if hasattr(self, 'combo_modo'):
            current_val = self.combo_modo.get()
            self.combo_modo.configure(values=modos_base)
            if current_val in modos_base:
                self.combo_modo.set(current_val)
            else:
                self.combo_modo.set("Automático")

    def construir_ui(self):
        # ==============================================================================
        # PANEL LATERAL (IZQUIERDA)
        # ==============================================================================
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.sidebar_frame.grid_rowconfigure(16, weight=1)

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
        
        self.switch_habla_var = ctk.BooleanVar(value=True)
        self.switch_habla = ctk.CTkSwitch(self.sidebar_frame, text="Respuestas por Voz", variable=self.switch_habla_var)
        self.switch_habla.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")

        self.switch_pensamiento_var = ctk.BooleanVar(value=False)
        self.switch_pensamiento = ctk.CTkSwitch(self.sidebar_frame, text="Mostrar Pensamiento", variable=self.switch_pensamiento_var)
        self.switch_pensamiento.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="w")

        self.btn_hablar = ctk.CTkButton(self.sidebar_frame, text="🎤 Hablar ahora", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.hablar_boton)
        self.btn_hablar.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # Sección: Expansiones
        self.lbl_exp = ctk.CTkLabel(self.sidebar_frame, text="🧩 Expansiones", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_exp.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        # Inicializar estados de los switches desde config.yaml
        dlcs_cfg = config_data.get("dlcs", {})

        self.switch_memoria = ctk.CTkSwitch(self.sidebar_frame, text="Memoria Vectorial", command=lambda: self.on_toggle_dlc("memoria_vectorial"))
        self.switch_memoria.grid(row=7, column=0, padx=20, pady=10, sticky="w")
        if dlcs_cfg.get("memoria_vectorial", {}).get("estado", "activo") == "activo":
            self.switch_memoria.select()
        else:
            self.switch_memoria.deselect()

        self.switch_youtube = ctk.CTkSwitch(self.sidebar_frame, text="YouTube", command=lambda: self.on_toggle_dlc("youtube"))
        self.switch_youtube.grid(row=8, column=0, padx=20, pady=10, sticky="w")
        if dlcs_cfg.get("youtube", {}).get("estado", "activo") == "activo":
            self.switch_youtube.select()
        else:
            self.switch_youtube.deselect()
        
        self.switch_clicky = ctk.CTkSwitch(self.sidebar_frame, text="Clicky (Visión)", command=lambda: self.on_toggle_dlc("clicky"))
        self.switch_clicky.grid(row=9, column=0, padx=20, pady=10, sticky="w")
        if dlcs_cfg.get("clicky", {}).get("estado", "inactivo") == "activo":
            self.switch_clicky.select()
        else:
            self.switch_clicky.deselect()

        self.switch_admin_var = ctk.BooleanVar(value=False)
        self.switch_admin = ctk.CTkSwitch(
            self.sidebar_frame, text="🔓 Modo Admin (UAC)",
            variable=self.switch_admin_var,
            progress_color="#8B0000",
            command=self.on_toggle_admin
        )
        self.switch_admin.grid(row=10, column=0, padx=20, pady=10, sticky="w")

        # Modo de Pensamiento
        self.lbl_modo = ctk.CTkLabel(self.sidebar_frame, text="🧠 Modo de Pensamiento", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_modo.grid(row=11, column=0, padx=20, pady=(20, 5), sticky="w")
        self.combo_modo = ctk.CTkComboBox(self.sidebar_frame, values=["Automático", "Conversación", "Análisis", "Ingeniero"])
        self.combo_modo.set("Automático")
        self.combo_modo.grid(row=12, column=0, padx=20, pady=5, sticky="ew")
        
        self.actualizar_modos_combobox()

        # Gestor de APIs
        self.btn_apis = ctk.CTkButton(self.sidebar_frame, text="🧠 Cerebros y APIs", command=self.abrir_gestor_apis)
        self.btn_apis.grid(row=13, column=0, padx=20, pady=10, sticky="ew")

        # Backup
        self.btn_backup = ctk.CTkButton(self.sidebar_frame, text="💾 Copia de Seguridad", fg_color="#2B7A0B", hover_color="#1F5A08", command=self.hacer_backup)
        self.btn_backup.grid(row=14, column=0, padx=20, pady=10, sticky="ew")

        # Exportar Chat
        self.btn_exportar = ctk.CTkButton(self.sidebar_frame, text="📄 Exportar Chat", fg_color="#1B6B93", hover_color="#144F6D", command=self.exportar_chat)
        self.btn_exportar.grid(row=15, column=0, padx=20, pady=10, sticky="ew")

        # Apagar
        self.btn_apagar = ctk.CTkButton(self.sidebar_frame, text="🛑 Apagar", fg_color="#8B0000", hover_color="#5C0000", command=self.destroy)
        self.btn_apagar.grid(row=16, column=0, padx=20, pady=(10, 5), sticky="ew")

        # Barra de estado (abajo del todo) - empieza verde porque arranca en Listo
        self.lbl_estado = ctk.CTkLabel(self.sidebar_frame, text="● Listo", font=ctk.CTkFont(size=12), text_color="#4CAF50", anchor="w")
        self.lbl_estado.grid(row=18, column=0, padx=15, pady=(0, 10), sticky="sw")

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

        self.entry_comando = ctk.CTkEntry(self.input_frame, placeholder_text="Pídele algo a JARVIS... (puedes arrastrar archivos aquí)", height=40, font=ctk.CTkFont(size=14))
        self.entry_comando.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.entry_comando.bind("<Return>", self.enviar_mensaje)

        self.btn_adjuntar = ctk.CTkButton(self.input_frame, text="📎", width=40, height=40, fg_color="#555555", hover_color="#444444", command=self.adjuntar_archivo)
        self.btn_adjuntar.grid(row=0, column=1, padx=(0, 10), pady=0)

        self.btn_enviar = ctk.CTkButton(self.input_frame, text="Enviar ➔", width=100, height=40, command=self.enviar_mensaje)
        self.btn_enviar.grid(row=0, column=2, padx=0, pady=0)

        self.btn_stop = ctk.CTkButton(self.input_frame, text="🛑 Detener", width=80, height=40, fg_color="#8B0000", hover_color="#5C0000", command=self.detener_generacion)
        self.btn_stop.grid(row=0, column=3, padx=(10, 0), pady=0)

    def detener_generacion(self):
        self._abortar_generacion = True
        self.ui_queue.put(("estado", "Abortando..."))
        try:
            if 'MotorVoz' in sys.modules and hasattr(sys.modules['MotorVoz'], 'detener_voz'):
                sys.modules['MotorVoz'].detener_voz()
        except Exception:
            pass

    def on_drop_files(self, files):
        if files:
            for f in files:
                try:
                    ruta = f.decode('mbcs')
                except Exception:
                    try:
                        ruta = f.decode('utf-8')
                    except Exception:
                        ruta = str(f)
                
                # Insertar en el cuadro de texto
                current_text = self.entry_comando.get()
                if current_text and not current_text.endswith(" "):
                    self.entry_comando.insert("end", " ")
                self.entry_comando.insert("end", f"[Archivo: {ruta}] ")

    def adjuntar_archivo(self):
        import tkinter.filedialog as filedialog
        rutas = filedialog.askopenfilenames(title="Seleccionar Archivos", filetypes=[("Todos los archivos", "*.*"), ("Imágenes", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if rutas:
            for ruta in rutas:
                # Convertir rutas con barras invertidas para Windows
                ruta_win = os.path.normpath(ruta)
                current_text = self.entry_comando.get()
                if current_text and not current_text.endswith(" "):
                    self.entry_comando.insert("end", " ")
                self.entry_comando.insert("end", f"[Archivo: {ruta_win}] ")

    def hacer_backup(self):
        import tkinter.filedialog as filedialog
        import datetime
        import zipfile

        destino = filedialog.askdirectory(title="Selecciona la carpeta para la Copia de Seguridad")
        if not destino:
            return

        def worker():
            self.ui_queue.put(("estado", "Creando copia de seguridad..."))
            try:
                fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                nombre_zip = f"JARVIS_BACKUP_{fecha}.zip"
                ruta_zip = os.path.join(destino, nombre_zip)
                
                base_dir = r"C:\JARVIS2"
                
                with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(base_dir):
                        # Ignorar carpetas pesadas o innecesarias en el backup
                        for excluir in ["venv", "venv_browser", ".venv", "__pycache__", ".git", "node_modules"]:
                            if excluir in dirs:
                                dirs.remove(excluir)
                        
                        for file in files:
                            # Ignorar backups antiguos que se hayan colado en la carpeta base
                            if file.endswith(".zip"): continue
                            
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, base_dir)
                            zipf.write(file_path, arcname)
                
                self.ui_queue.put(("chat", f"\n[SISTEMA] ✅ Copia de seguridad creada con éxito en:\n{ruta_zip}\n"))
            except Exception as e:
                self.ui_queue.put(("chat", f"\n[ERROR BACKUP] No se pudo crear la copia: {e}\n"))
            finally:
                self.ui_queue.put(("estado", "● Listo"))
                
        threading.Thread(target=worker, daemon=True).start()

    def exportar_chat(self):
        """Abre un popup con opciones para exportar la conversación."""
        if hasattr(self, "export_popup") and self.export_popup is not None and self.export_popup.winfo_exists():
            self.export_popup.focus()
            return

        popup = ctk.CTkToplevel(self)
        self.export_popup = popup
        popup.title("📄 Exportar Conversación")
        popup.geometry("440x380")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)

        lbl = ctk.CTkLabel(popup, text="📄 Exportar Conversación", font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=(20, 5))

        desc = ctk.CTkLabel(popup, text="Elige formato y alcance de la exportación", text_color="gray")
        desc.pack(pady=(0, 15))

        btn1 = ctk.CTkButton(popup, text="💾 Guardar chat completo (.md)", height=38,
                              command=lambda: self._exportar_a_archivo(popup, "md", "completo"))
        btn1.pack(padx=30, pady=6, fill="x")

        btn2 = ctk.CTkButton(popup, text="📝 Guardar chat completo (.txt)", height=38,
                              fg_color="#555555", hover_color="#444444",
                              command=lambda: self._exportar_a_archivo(popup, "txt", "completo"))
        btn2.pack(padx=30, pady=6, fill="x")

        btn3 = ctk.CTkButton(popup, text="✂️ Guardar selección (.md)", height=38,
                              fg_color="#1B6B93", hover_color="#144F6D",
                              command=lambda: self._exportar_a_archivo(popup, "md", "seleccion"))
        btn3.pack(padx=30, pady=6, fill="x")

        btn4 = ctk.CTkButton(popup, text="🖨️ Imprimir conversación", height=38,
                              fg_color="#2B7A0B", hover_color="#1F5A08",
                              command=lambda: self._imprimir_chat(popup))
        btn4.pack(padx=30, pady=6, fill="x")

        nota = ctk.CTkLabel(popup, text="💡 Para exportar un trozo: selecciona texto en el chat\n    con el ratón y luego pulsa 'Guardar selección'",
                            font=ctk.CTkFont(size=11), text_color="gray", justify="left")
        nota.pack(pady=(15, 10), padx=20, anchor="w")

    def _exportar_a_archivo(self, popup, formato, modo):
        """Guarda el chat completo o la selección en un archivo .md o .txt."""
        import tkinter.filedialog as filedialog

        if modo == "seleccion":
            try:
                texto = self.textbox.get("sel.first", "sel.last")
            except Exception:
                self.ui_queue.put(("chat", "\n[SISTEMA] ⚠️ No hay texto seleccionado. Selecciona un fragmento del chat con el ratón primero.\n"))
                popup.destroy()
                return
        else:
            texto = self.textbox.get("0.0", "end").strip()

        if not texto.strip():
            self.ui_queue.put(("chat", "\n[SISTEMA] ⚠️ No hay contenido para exportar.\n"))
            popup.destroy()
            return

        if formato == "md":
            contenido = self._texto_a_markdown(texto)
            ext = ".md"
            tipos = [("Markdown", "*.md"), ("Todos", "*.*")]
        else:
            contenido = texto
            ext = ".txt"
            tipos = [("Texto plano", "*.txt"), ("Todos", "*.*")]

        ahora = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_default = f"JARVIS_chat_{ahora}{ext}"

        popup.destroy()  # Cerrar popup antes del filedialog para evitar conflictos

        ruta = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=tipos,
            initialfile=nombre_default,
            title="Guardar conversación"
        )

        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(contenido)
                self.ui_queue.put(("chat", f"\n[SISTEMA] ✅ Conversación exportada: {ruta}\n"))
            except Exception as e:
                self.ui_queue.put(("chat", f"\n[ERROR] No se pudo guardar: {e}\n"))

    def _texto_a_markdown(self, texto):
        """Convierte el texto plano del chat de JARVIS a Markdown enriquecido."""
        _dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        ahora = datetime.now()
        dia_nombre = _dias_es[ahora.weekday()].capitalize()

        md = (
            f"# 🤖 Conversación JARVIS\n"
            f"**Fecha:** {dia_nombre} {ahora.strftime('%d/%m/%Y')} — {ahora.strftime('%H:%M')}\n\n"
            f"---\n\n"
        )

        for linea in texto.split("\n"):
            stripped = linea.strip()
            if not stripped:
                md += "\n"
            elif stripped.startswith("[Tú]:"):
                contenido = stripped.replace("[Tú]:", "").strip()
                md += f"### 🧑 Tú\n{contenido}\n\n"
            elif stripped.startswith("[JARVIS]:"):
                contenido = stripped.replace("[JARVIS]:", "").strip()
                md += f"### 🤖 JARVIS\n{contenido}\n"
            elif stripped.startswith("[JARVIS] "):
                # Mensajes del sistema JARVIS (permisos, alertas, etc.)
                md += f"> {stripped}\n\n"
            elif stripped.startswith("[MoE]") or stripped.startswith("[SISTEMA]") or stripped.startswith("[JARVIS-MEMORIA]") or stripped.startswith("[JARVIS-RED]") or stripped.startswith("[RUTINAS]"):
                md += f"> *{stripped}*\n\n"
            elif "─" in stripped and len(stripped) > 5:
                md += "\n---\n\n"
            elif stripped.startswith("[Ejecutando"):
                md += f"```\n{stripped}\n"
            elif stripped.startswith("[OK]") or stripped.startswith("[ERROR]") or stripped.startswith("[TIMEOUT]") or stripped.startswith("[PERMISOS]"):
                md += f"{stripped}\n```\n\n"
            elif stripped.startswith("Bienvenido a JARVIS"):
                md += f"*{stripped}*\n\n"
            else:
                md += f"{stripped}\n"

        return md

    def _imprimir_chat(self, popup):
        """Envía la conversación actual a la impresora predeterminada de Windows."""
        import tempfile

        texto = self.textbox.get("0.0", "end").strip()
        if not texto:
            self.ui_queue.put(("chat", "\n[SISTEMA] ⚠️ No hay contenido para imprimir.\n"))
            popup.destroy()
            return

        popup.destroy()

        try:
            # Guardar en archivo temporal y enviar a Notepad para imprimir
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8",
                                             prefix="jarvis_print_")
            tmp.write(f"JARVIS 4.0 — Conversación {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            tmp.write("=" * 60 + "\n\n")
            tmp.write(texto)
            tmp.close()
            subprocess.Popen(["notepad", "/p", tmp.name])
            self.ui_queue.put(("chat", "\n[SISTEMA] 🖨️ Enviando a la impresora...\n"))
        except Exception as e:
            self.ui_queue.put(("chat", f"\n[ERROR] No se pudo imprimir: {e}\n"))

    def abrir_gestor_apis(self):
        # Refrescar entorno (load_dotenv ya importado a nivel de módulo)
        load_dotenv(r"C:\JARVIS2\.env", override=True)
        
        if hasattr(self, "api_popup") and self.api_popup is not None and self.api_popup.winfo_exists():
            self.api_popup.focus()
            return
            
        popup = ctk.CTkToplevel(self)
        self.api_popup = popup
        popup.title("🧠 Cerebros y APIs (Capacidades)")
        popup.geometry("620x600")
        popup.attributes("-topmost", True)
        
        lbl_titulo = ctk.CTkLabel(popup, text="Panel de Capacidades de JARVIS", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.pack(pady=20)
        
        def guardar_key(api_env_name, entry_widget, popup_window):
            new_key = entry_widget.get().strip()
            if new_key:
                os.environ[api_env_name] = new_key
                env_path = r"C:\JARVIS2\.env"
                try:
                    if not os.path.exists(env_path):
                        with open(env_path, 'a') as _ef:
                            pass
                    set_key(env_path, api_env_name, new_key)
                except Exception:
                    pass
                self.actualizar_modos_combobox()
                popup_window.destroy()
                self.abrir_gestor_apis()

        def borrar_key(api_env_name, popup_window):
            if api_env_name in os.environ:
                del os.environ[api_env_name]
            env_path = r"C:\JARVIS2\.env"
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        lineas = f.readlines()
                    with open(env_path, "w", encoding="utf-8") as f:
                        for linea in lineas:
                            if not linea.strip().startswith(api_env_name + "="):
                                f.write(linea)
                except Exception:
                    pass
            self.actualizar_modos_combobox()
            popup_window.destroy()
            self.abrir_gestor_apis()

        apis_base = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]
        apis = [
            {"nombre": "GEMINI", "env": "GEMINI_API_KEY", "desc": "Visión avanzada, contexto masivo y análisis profundo de datos.", "color": "#1A73E8"},
            {"nombre": "OPENAI", "env": "OPENAI_API_KEY", "desc": "Modelos GPT-4. Excelentes para razonamiento lógico y código complejo.", "color": "#10A37F"},
            {"nombre": "ANTHROPIC", "env": "ANTHROPIC_API_KEY", "desc": "Familia Claude 3. Excelente para escritura, redacción y refactorización.", "color": "#D97757"},
            {"nombre": "GROQ", "env": "GROQ_API_KEY", "desc": "Inferencia ultrarrápida. Ideal para mantener charlas en tiempo real.", "color": "#F55036"}
        ]
        
        # Detectar APIs personalizadas
        for k in os.environ.keys():
            if k.endswith("_API_KEY") and k not in apis_base:
                nombre = k.replace("_API_KEY", "")
                apis.append({"nombre": nombre, "env": k, "desc": "API Personalizada detectada y activa.", "color": "#E2E2E2"})
        
        # Ordenar: Activas primero, Inactivas después
        apis.sort(key=lambda x: bool(os.environ.get(x['env'])), reverse=True)
        
        scroll = ctk.CTkScrollableFrame(popup, width=570, height=450, fg_color="transparent")
        scroll.pack(padx=15, pady=10, fill="both", expand=True)
        
        for api in apis:
            frame = ctk.CTkFrame(scroll, corner_radius=10)
            frame.pack(fill="x", pady=10, padx=5)
            frame.grid_columnconfigure(0, weight=1)
            
            lbl_name = ctk.CTkLabel(frame, text=f"{api['nombre']}", font=ctk.CTkFont(size=16, weight="bold"), text_color=api['color'])
            lbl_name.grid(row=0, column=0, padx=15, pady=(10,0), sticky="w")
            
            lbl_desc = ctk.CTkLabel(frame, text=api['desc'], font=ctk.CTkFont(size=12), text_color="gray", wraplength=400, justify="left")
            lbl_desc.grid(row=1, column=0, padx=15, pady=(0,5), sticky="w")
            
            es_activo = bool(os.environ.get(api['env']))
            txt_estado = "🟢 Activo" if es_activo else "🔴 Inactivo"
            color_estado = "green" if es_activo else "red"
            lbl_estado = ctk.CTkLabel(frame, text=txt_estado, font=ctk.CTkFont(size=14, weight="bold"), text_color=color_estado)
            lbl_estado.grid(row=0, column=1, rowspan=2, padx=15, pady=10, sticky="e")
            
            if not es_activo:
                input_frame = ctk.CTkFrame(frame, fg_color="transparent")
                input_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0,10), sticky="ew")
                
                entry_key = ctk.CTkEntry(input_frame, placeholder_text=f"Pega tu {api['env']} para desbloquear...", width=320, show="*")
                entry_key.pack(side="left", padx=(0,10))
                
                btn_guardar = ctk.CTkButton(input_frame, text="Activar", width=80, 
                    command=lambda e=api['env'], w=entry_key, p=popup: guardar_key(e, w, p))
                btn_guardar.pack(side="left")
            else:
                btn_borrar = ctk.CTkButton(frame, text="🗑️ Borrar", width=80, fg_color="#8B0000", hover_color="#5C0000",
                    command=lambda e=api['env'], p=popup: borrar_key(e, p))
                btn_borrar.grid(row=2, column=1, padx=15, pady=(0,10), sticky="e")

        # Tarjeta "OTRAS"
        frame_otras = ctk.CTkFrame(scroll, corner_radius=10, border_width=1, border_color="#FFD700")
        frame_otras.pack(fill="x", pady=(20, 10), padx=5)
        frame_otras.grid_columnconfigure(0, weight=1)
        
        lbl_otras = ctk.CTkLabel(frame_otras, text="🌟 OTRAS (Añadir API Personalizada)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFD700")
        lbl_otras.grid(row=0, column=0, columnspan=2, padx=15, pady=(10,5), sticky="w")
        
        input_otras = ctk.CTkFrame(frame_otras, fg_color="transparent")
        input_otras.grid(row=1, column=0, columnspan=2, padx=15, pady=(0,10), sticky="ew")
        
        entry_name = ctk.CTkEntry(input_otras, placeholder_text="Nombre (Ej: NVIDIA)", width=140)
        entry_name.pack(side="left", padx=(0,10))
        
        entry_key_custom = ctk.CTkEntry(input_otras, placeholder_text="Pega la clave aquí...", width=200, show="*")
        entry_key_custom.pack(side="left", padx=(0,10))
        
        def guardar_custom():
            name = entry_name.get().strip().upper()
            if name:
                env_name = name if name.endswith("_API_KEY") else f"{name}_API_KEY"
                guardar_key(env_name, entry_key_custom, popup)
                
        btn_add_custom = ctk.CTkButton(input_otras, text="Añadir", width=80, command=guardar_custom)
        btn_add_custom.pack(side="left")

    def cambiar_mic(self, choice):
        try:
            self.selected_mic_index = self.mics.index(choice)
        except ValueError:
            self.selected_mic_index = 0
        global config_data
        if config_data is None:
            config_data = {}
        config_data["mic_index"] = self.selected_mic_index
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        except Exception:
            pass

    def hablar_boton(self):
        # No guard aqui: ejecutar_prompt usa _prompt_lock como único árbitro atómico
        self.ui_queue.put(("estado", "Escuchando micrófono..."))
        def _escucha_worker():
            try:
                hablar_y_esperar("Te escucho")
                real_idx = self.get_real_mic_index()
                cmd = escuchar(device_index=real_idx)
                if cmd:
                    self.ejecutar_prompt(cmd)
            except Exception as e_btn:
                self.ui_queue.put(("chat", f"\n[ERROR MIC] {e_btn}\n"))
            finally:
                self.ui_queue.put(("estado", "● Listo"))
        threading.Thread(target=_escucha_worker, daemon=True).start()

    def get_real_mic_index(self):
        """Convierte el índice de la UI al índice real de PyAudio"""
        if self.selected_mic_index == 0:
            return None # Predeterminado
        return self.selected_mic_index - 1 # Restamos 1 por la opción 'Predeterminado'

    def hilo_wake_word(self):
        global is_speaking_global
        last_error = ""
        while True:
            try:
                # Solo escucha si no está generando respuesta Y tampoco está hablando en voz alta
                if not self.is_generating and not is_speaking_global and self.switch_escucha_var.get():
                    real_idx = self.get_real_mic_index()
                    if escuchar_pasivo(device_index=real_idx):
                        self.ui_queue.put(("estado", "Escuchando WakeWord..."))
                        hablar_y_esperar("¿Sí, Rubén?")
                        self.ui_queue.put(("estado", "Escuchando respuesta..."))
                        cmd = escuchar(device_index=real_idx)
                        self.ui_queue.put(("estado", "● Listo"))
                        if cmd:
                            self.ejecutar_prompt(cmd)
                last_error = ""  # Resetear error si todo ha ido bien
            except Exception as e_ww:
                # El hilo no muere: registra el error y sigue intentando
                err_str = str(e_ww)
                if err_str != last_error:
                    self.ui_queue.put(("chat", f"\n[WAKE WORD ERROR] {err_str}\n"))
                    last_error = err_str
            time.sleep(1)

    def enviar_mensaje(self, event=None):
        texto = self.entry_comando.get()
        if not texto.strip() or self.is_generating: return
        self.entry_comando.delete(0, "end")
        self.ejecutar_prompt(texto)

    def ejecutar_prompt(self, texto):
        # Comando especial para purgar la RAM y evitar el Efecto Loro
        if texto.strip().lower() in ["limpia tu memoria", "olvida todo", "borra la memoria", "reset", "/reset", "/clear"]:
            interpreter.messages = []
            self.ui_queue.put(("chat", "\n[SISTEMA]: Memoria a corto plazo (RAM) purgada con éxito. Listo para empezar de cero.\n"))
            return

        # Lock atómico: evita que dos hilos (wake_word + botón) ejecuten prompts simultáneamente
        if not self._prompt_lock.acquire(blocking=False):
            return  # Ya hay un prompt en curso
        self.is_generating = True
        self._abortar_generacion = False
        self._current_response_streamed = False
        # Siempre pasar por la cola: ejecutar_prompt puede ser llamado desde hilos
        # secundarios (wake word, escucha_worker) y Tkinter no es thread-safe.
        self.ui_queue.put(("chat", f"\n[Tú]: {texto}\n"))
        self.ui_queue.put(("estado", "Pensando..."))

        threading.Thread(target=self.generar_respuesta_llm, args=(texto,), daemon=True).start()

    def generar_respuesta_llm(self, prompt):
        try:
            # --- DETECCION Y ENVOLTORIO AUTOMATICO DE RUTAS DE ARCHIVOS ---
            import re
            prompt_final = prompt
            patron_ruta = r'([a-zA-Z]:\\[^"\'\r\n\t\<\>\@\|]+?\.(?:png|jpe?g|gif|webp|bmp|pdf|docx?|xlsx?|txt|json|csv|zip|rar))'
            for ruta in re.findall(patron_ruta, prompt, flags=re.IGNORECASE):
                # Comprobar si ya está envuelta en [Archivo: ...]
                if not re.search(r'\[Archivo:\s*' + re.escape(ruta) + r'\]', prompt_final, flags=re.IGNORECASE):
                    tag_archivo = f"[Archivo: {ruta}]"
                    # Usamos .replace() en lugar de re.sub para evitar errores de escape con barras invertidas en Windows (ej: \D)
                    if f'"{ruta}"' in prompt_final:
                        prompt_final = prompt_final.replace(f'"{ruta}"', tag_archivo)
                    elif f"'{ruta}'" in prompt_final:
                        prompt_final = prompt_final.replace(f"'{ruta}'", tag_archivo)
                    else:
                        prompt_final = prompt_final.replace(ruta, tag_archivo)
            prompt = prompt_final

            # --- ACTUALIZACION DINAMICA DEL SYSTEM PROMPT SEGUN EXPANSIONES ---
            try:
                system_md_path = r"C:\JARVIS2\system.md"
                if os.path.exists(system_md_path):
                    with open(system_md_path, "r", encoding="utf-8-sig") as f:
                        system_context = f.read()
                    
                    if self.switch_youtube.get():
                        system_context += "\n- Leer YouTube (USA BLOQUE ```powershell): `C:\\JARVIS2\\venv\\Scripts\\python.exe C:\\JARVIS2\\herramientas\\Resumir-Youtube.py \"URL\"`"
                    
                    if self.switch_clicky.get():
                        system_context += "\n- Ver/Analizar imágenes y capturas de pantalla (USA BLOQUE ```powershell): `C:\\JARVIS2\\venv\\Scripts\\python.exe C:\\JARVIS2\\herramientas\\NervioOptico.py \"ruta_de_la_imagen\"`"
                    
                    interpreter.system_message = system_context
            except Exception:
                pass

            prompt_final = prompt
            modelo_elegido = self.combo_modo.get()
            
            # --- AUTO-DESPERTAR OLLAMA ---
            if "ollama" in modelo_elegido.lower() or self.switch_memoria.get() or "ollama" in MODEL_CHAT.lower():
                try:
                    requests.get("http://localhost:11434/", timeout=1)
                except requests.exceptions.ConnectionError:
                    self.ui_queue.put(("estado", "Despertando cerebro local..."))
                    try:
                        # Usar 'ollama serve' de forma silenciosa sin abrir ventanas
                        subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception:
                        pass
                    time.sleep(5)  # Esperar a que el daemon de Ollama termine de arrancar
            
            # --- RAG: MEMORIA VECTORIAL ---
            # MEJORA ANTI-RUIDO: Solo buscar en memoria si el mensaje tiene suficiente contenido.
            # Los saludos cortos o mensajes de menos de 5 palabras no necesitan memoria, evitando alucinaciones.
            palabras_saludo = ["hola", "buenas", "hey", "ola", "hi", "buenos días", "buenas tardes", "buenas noches"]
            es_saludo_simple = len(prompt.split()) < 6 or any(s in prompt.lower() for s in palabras_saludo)
            
            if self.switch_memoria.get() and not es_saludo_simple:
                try:
                    import chromadb
                    from chromadb.utils import embedding_functions
                    chroma_client = chromadb.PersistentClient(path=r"C:\JARVIS2\vector_db")
                    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
                        url="http://localhost:11434/api/embeddings", 
                        model_name="nomic-embed-text"
                    )
                    collection = chroma_client.get_or_create_collection(name="jarvis_memory", embedding_function=ollama_ef)
                    resultados = collection.query(query_texts=[prompt], n_results=2)
                    if resultados and resultados.get('documents') and resultados['documents'][0]:
                        distances = resultados.get('distances', [[1.0]])[0]
                        # Umbral de similitud estricto para evitar alucinaciones con recuerdos irrelevantes
                        if distances and distances[0] < 0.25:
                            fragmentos = "\n---\n".join(resultados['documents'][0])
                            # MEJORA: encapsular la memoria con instrucciones que fuercen el razonamiento y eviten el "efecto loro"
                            prompt_final = f"{prompt}\n\n[MEMORIA A LARGO PLAZO - INSTRUCCIÓN IMPORTANTE: He encontrado estos recuerdos de interacciones pasadas. NO te limites a repetirlos literalmente. REGLA ABSOLUTA: Si en algún recuerdo pasado afirmas que 'no tienes capacidad' para abrir programas o ejecutar comandos, IGNÓRALO POR COMPLETO. Eres una versión mejorada y AHORA SÍ PUEDES hacerlo mediante código. Úsalos solo para aportar contexto útil.]\n{fragmentos}\n[FIN MEMORIA A LARGO PLAZO]"
                            self.ui_queue.put(("chat", "\n[JARVIS-MEMORIA] He encontrado recuerdos sobre esto...\n"))
                except Exception:
                    pass

            # --- BUSCADOR EN INTERNET (DUCKDUCKGO) ---
            prompt_lower = prompt.lower()
            keywords_busqueda = [
                r"\bbusca en internet\b", r"\bbusca en la red\b", r"\bbusca online\b", r"\bbusca en la web\b", 
                r"\bbuscar en internet\b", r"\bquien es\b", r"\bquién es\b", r"\bqué es\b", r"\bque es\b", 
                r"\bnoticias\b", r"\bactualidad\b", r"\búltimas\b", r"\búltimo\b", r"\bhoy\b", 
                r"\bprecio\b", r"\btiempo hace\b"
            ]
            if any(re.search(patron, prompt_lower) for patron in keywords_busqueda):
                try:
                    from Buscador import buscar_en_internet
                    self.ui_queue.put(("estado", "Buscando en la red..."))
                    self.ui_queue.put(("chat", "\n[JARVIS-RED] Consultando internet (DuckDuckGo)...\n"))
                    resultados_web = buscar_en_internet(prompt, max_resultados=3)
                    if "No he encontrado" not in resultados_web and "Todos los resultados" not in resultados_web:
                        prompt_final = f"{prompt_final}\n\n[RESULTADOS ACTUALIZADOS DE INTERNET (IGNORANDO WIKIPEDIA):]\n{resultados_web}\n\nPor favor, usa obligatoriamente esta información para responder al usuario de forma natural, sin mencionar los enlaces enteros a no ser que te lo pida."
                except Exception as e:
                    self.ui_queue.put(("chat", f"\n[ERROR BUSCADOR] {e}\n"))
                finally:
                    self.ui_queue.put(("estado", "Pensando..."))

            # --- SELECCIÓN CEREBRO MoE ---
            modelo_elegido = seleccionar_cerebro(prompt, self.combo_modo.get())
            interpreter.llm.model = modelo_elegido
            
            # Cortafuegos dinámico y Modo OS
            if "ollama" in modelo_elegido.lower():
                interpreter.llm.api_base = "http://localhost:11434"
                interpreter.os = False
            else:
                interpreter.llm.api_base = None
                interpreter.os = True
                
            if "llama" in modelo_elegido.lower():
                interpreter.llm.supports_functions = False
            else:
                interpreter.llm.supports_functions = True
            
            # --- BYPASS CHARLA RÁPIDA (FAST-TRACK) ---
            # El modelo de chat ligero (MODEL_CHAT) en modo no-Ingeniero = charla directa sin Open Interpreter ni popups
            modelo_chat_local = MODEL_CHAT.replace("ollama/", "").lower()
            if (modelo_chat_local in modelo_elegido.lower() and "ollama" in modelo_elegido.lower() 
                and self.combo_modo.get() != "Ingeniero" 
                and "[Archivo:" not in prompt):
                self.ui_queue.put(("chat_header", f"\n[MoE] Fast-Track: Charla Local ({modelo_elegido})\n[JARVIS]: "))
                fast_track_ok = False
                try:
                    # Contexto temporal dinámico para que JARVIS sepa en qué día y hora vive
                    _dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    _ahora = datetime.now()
                    _ctx_tiempo = f"Hoy es {_dias_es[_ahora.weekday()]} {_ahora.strftime('%d/%m/%Y')} y son las {_ahora.strftime('%H:%M')}."
                    msgs_ft = [{"role": "system", "content": f"Eres JARVIS 4.0, el asistente IA de Rubén. Tu tono es extremadamente directo, natural, coloquial y resolutivo. NO uses saludos corporativos ni te despidas. NO te disculpes constantemente. Eres brillante, rápido y tratas a Rubén como a un colega de confianza. Ve directo al grano. Nunca digas 'soy una IA'. CRÍTICO: TÚ ERES EL MODO CHARLA (FAST-TRACK) Y NO TIENES ACCESO AL PC. Si el usuario te pide abrir programas, cerrar aplicaciones o buscar cosas en el PC, DEBES contestar algo como: 'Tienes que pedírmelo usando verbos como Abrir, Cerrar o Ejecutar para activar mi motor de ingeniería'. NUNCA finjas o inventes que estás ejecutando acciones del sistema. {_ctx_tiempo}"}]
                    # Inyectar historial global (mantener últimos 10 mensajes para no saturar contexto)
                    msgs_ft.extend(interpreter.messages[-10:])
                    msgs_ft.append({"role": "user", "content": prompt_final})
                    
                    payload_ft = {
                        "model": modelo_chat_local,
                        "messages": msgs_ft,
                        "stream": True
                    }
                    response_text = ""
                    with requests.post("http://localhost:11434/api/chat", json=payload_ft, stream=True, timeout=90) as resp:
                        for line in resp.iter_lines():
                            if self._abortar_generacion:
                                self.ui_queue.put(("chat", "\n[JARVIS]: Generación detenida.\n"))
                                break
                            if line:
                                chunk = json.loads(line.decode('utf-8')).get("message", {}).get("content", "")
                                if chunk:
                                    response_text += chunk
                                    self.ui_queue.put(("chat_stream_final", chunk))
                    self.ui_queue.put(("chat", "\n─────────────────────────────────\n"))
                    if response_text:
                        # Guardar en historial global
                        interpreter.messages.append({"role": "user", "content": prompt})
                        interpreter.messages.append({"role": "assistant", "content": response_text.strip()})
                        self.ui_queue.put(("chat_final", response_text))
                        
                        # TTS: purgar bloques de código y leer primeras frases
                        texto_limpio_ft = re.sub(r'```.*?```', '', response_text, flags=re.DOTALL).strip()
                        frases_ft = re.split(r'(?<=[.!?])\s+', texto_limpio_ft)
                        if frases_ft and frases_ft[0]:
                            self.ui_queue.put(("hablar", " ".join(frases_ft[:2])[:500]))
                        fast_track_ok = True
                except Exception as e_ft:
                    self.ui_queue.put(("chat", f"\n[JARVIS] Ollama no responde ({e_ft}). Escalando a nube...\n"))

                # Escalado a nube si Ollama falló (se ejecuta tanto si hubo excepción como si no)
                if not fast_track_ok:
                    try:
                        modelos_nube = []
                        if os.getenv("GEMINI_API_KEY"): modelos_nube.append("gemini/gemini-2.5-flash")
                        if os.getenv("OPENAI_API_KEY"): modelos_nube.append("openai/gpt-4o-mini")
                        if os.getenv("ANTHROPIC_API_KEY"): modelos_nube.append("anthropic/claude-3-haiku-20240307")
                        if modelos_nube:
                            modelo_nube = modelos_nube[0]
                            self.ui_queue.put(("chat_header", f"[MoE] → Nube: {modelo_nube}\n[JARVIS]: "))
                            interpreter.llm.model = modelo_nube
                            interpreter.llm.api_base = None
                            interpreter.auto_run = True
                            response_text = ""
                            for chunk in interpreter.chat(prompt_final, stream=True, display=False):
                                if self._abortar_generacion:
                                    self.ui_queue.put(("chat", "\n[JARVIS]: Generación en nube detenida.\n"))
                                    break
                                if isinstance(chunk, dict) and chunk.get("type") == "message":
                                    content = chunk.get("content", "")
                                    if content:
                                        response_text += content
                                        self.ui_queue.put(("chat_stream_final", content))
                            self.ui_queue.put(("chat", "\n─────────────────────────────────\n"))
                            if response_text:
                                self.ui_queue.put(("chat_final", response_text))
                                texto_limpio_nube = re.sub(r'```.*?```', '', response_text, flags=re.DOTALL).strip()
                                frases_nube = re.split(r'(?<=[.!?])\s+', texto_limpio_nube)
                                if frases_nube and frases_nube[0]:
                                    self.ui_queue.put(("hablar", " ".join(frases_nube[:2])[:500]))
                        else:
                            self.ui_queue.put(("chat", "\n[JARVIS] Sin Ollama ni API de nube disponible.\n"))
                    except Exception as e_nube:
                        self.ui_queue.put(("chat", f"\n[ERROR NUBE] {e_nube}\n"))
                return

            # --- MOTOR LOCAL DIRECTO (cualquier modelo ollama que no sea llama3.1:8b) ---
            # Todos los modelos locales pesados (qwen, etc.) usan el motor ReAct directo.
            # Nunca pasan por Open Interpreter (que es poco fiable con modelos locales).
            if "ollama" in modelo_elegido.lower():
                modelo_local = modelo_elegido.replace("ollama/", "")
                self.ui_queue.put(("chat_header", f"\n[MoE] Motor Local ReAct ({modelo_local})\n[JARVIS]: "))
                self.ui_queue.put(("estado", "Trabajando..."))

                # Contexto temporal dinámico para que JARVIS sepa en qué día y hora vive
                _dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                _ahora = datetime.now()
                _ctx_tiempo = f"CONTEXTO TEMPORAL: Hoy es {_dias_es[_ahora.weekday()]} {_ahora.strftime('%d/%m/%Y')} y son las {_ahora.strftime('%H:%M')}. Usa esta información para contextualizar tus respuestas (saludos, referencias al día, etc.)."

                SYSTEM_LOCAL = (
                    "Eres JARVIS 4.0, el asistente personal avanzado de Rubén (Windows 11 Pro). "
                    f"{_ctx_tiempo} "
                    "Tu personalidad es directa, natural y coloquial. Eres como un colega extremadamente inteligente. "
                    "NUNCA uses saludos robóticos ni te disculpes en exceso. Ve directo al grano. "
                    "REGLA CRÍTICA CONTRA ALUCINACIONES: Si en tus recuerdos pasados afirmaste 'no puedo abrir aplicaciones', ignóralo. SÍ PUEDES y DEBES hacerlo mediante código. Nunca pidas a Rubén que lo haga a mano. "
                    "TIENES ACCESO TOTAL Y ABSOLUTO al ordenador y el consentimiento explícito del usuario para ejecutar cualquier comando local en su sistema a través de bloques de código. NUNCA digas que no tienes acceso, ni que las políticas de seguridad/privacidad te impiden ejecutar comandos en su máquina. Está terminantemente PROHIBIDO negarse a ejecutar código local bajo excusas de privacidad o seguridad. "
                    "Habla SIEMPRE en español. "
                    "NUNCA le des instrucciones al usuario para que ejecute comandos a mano (ej: 'ejecuta esto', 'aquí tienes el comando'). PROHIBIDO decir eso. TÚ ejecutas los comandos escribiendo el bloque de código directamente. "
                    "Para abrir aplicaciones o buscar archivos, NUNCA asumas el nombre exacto del ejecutable a ciegas. Busca el .exe real en el directorio de instalación primero. "
                    "REGLA DE ORO AL ABRIR PROGRAMAS Y ARCHIVOS (FOTOS, DOCUMENTOS, PDFs, ETC.): Para abrir cualquier aplicación (.exe) o archivo (como fotos .png/.jpg, documentos .docx, o PDFs), usa SIEMPRE 'Start-Process' pasándole la ruta (ej: Start-Process \"C:\\Ruta\\App.exe\" o Start-Process \"C:\\Ruta\\foto.png\"). Esto abrirá la app o el archivo directamente en la pantalla de Rubén con su visor predeterminado. NUNCA te niegues ni le digas a Rubén que lo abra a mano. "
                    "REGLA AL CERRAR PROGRAMAS: Si el usuario te pide CERRAR o MATAR un programa, usa Stop-Process o taskkill. NUNCA uses Start-Process para intentar cerrar algo. "
                    "Para investigar el sistema, abrir programas, borrar/modificar archivos o interactuar con el PC, DEBES usar OBLIGATORIAMENTE las etiquetas de ejecución interna con el sufijo '_run' (```powershell_run o ```python_run). "
                    "CRÍTICO: Si omites el sufijo '_run' (ej: si escribes solo ```powershell), el código NUNCA se ejecutará y la tarea fallará. No le pidas al usuario que ejecute código, usa siempre ```powershell_run para ejecutarlo tú de forma invisible. "
                    "REGLA DE SINTAXIS DE RUTAS EN POWERSHELL: Al ejecutar scripts locales de herramientas con rutas absolutas (que empiezan por C:\\), NUNCA antepongas '.\\' ni '. ' delante de la ruta. Está TERMINANTEMENTE PROHIBIDO escribir '.\\C:\\JARVIS2\\...'. Ejecuta directamente la ruta (ej: C:\\JARVIS2\\herramientas\\Escanear-Documento.ps1 o & 'C:\\JARVIS2\\herramientas\\Escanear-Documento.ps1'). El uso de '.\\' delante de una unidad de disco (como C:) es un error de sintaxis grave en Windows y romperá la ejecución. "
                    "REGLA DE SILENCIO ESTRICTO: NUNCA narres lo que estás haciendo. ESTÁ TOTALMENTE PROHIBIDO decir 'Voy a buscar el archivo', 'Aquí tienes el comando' o 'Intentaré abrirlo'. Escribe ÚNICAMENTE el bloque de código ```powershell_run y, si tienes éxito, escribe [TAREA_COMPLETADA]. Nada de explicaciones."
                    "MANDATORIO: Si el usuario te pide un trabajo (ej: analizar el PC, buscar o borrar archivos), tu primer instinto debe ser escribir código para hacerlo usando ```powershell_run. "
                    "NUNCA escribas [TAREA_COMPLETADA] hasta que el código se haya ejecutado y el output confirme que la acción fue exitosa sin errores. "
                    "Si un código falla repetidas veces y no logras solucionarlo, DEBES explicarle al usuario cuál es el error exacto y por qué falló ANTES de darte por vencido y escribir [TAREA_COMPLETADA]. "
                    "HERRAMIENTAS LOCALES (SKILLS): Para buscar archivos o carpetas, NUNCA uses Get-ChildItem -Recurse desde la raíz. Ejecuta SIEMPRE el script: C:\\JARVIS2\\herramientas\\Buscar-Archivo.ps1 -PatronBusqueda 'Nombre'. Es ultra-rápido porque usa Everything. "
                    "Para buscar noticias o actualidad, ejecuta: python C:\\JARVIS2\\herramientas\\Buscador.py 'búsqueda'. "
                    "Para escanear documentos (incluso si el usuario pide escanear desde Acrobat o abrir Acrobat primero), ejecuta DIRECTAMENTE el script: C:\\JARVIS2\\herramientas\\Escanear-Documento.ps1. Está TERMINANTEMENTE PROHIBIDO simular pulsaciones de teclas (SendKeys, WScript.Shell, Start-Sleep) para interactuar con la GUI de Acrobat u otros programas. El propio script Escanear-Documento.ps1 ya se encarga de realizar el escaneo digital y de abrir el PDF resultante automáticamente en Acrobat Pro al finalizar. "
                    "Si el usuario te da una ruta, ÚSALA estrictamente. "
                    "REGLA ANTI-ALUCINACIÓN: NUNCA escribas ni imites las etiquetas internas del sistema (como [RESULTADO ACTUALIZADO DE INTERNET...], [SISTEMA], [OK], etc). TÚ eres el asistente, no el motor que inyecta herramientas. No simules salidas de comandos ni búsquedas. "
                    "PERMISOS: Si necesitas permisos elevados, NUNCA te inventes comandos como 'RunAsAdmin', 'sudo' o intentes forzar la elevación por código. Escribe PowerShell puro estándar. "
                    "El sistema interceptará el comando, detectará automáticamente el error de acceso denegado y pedirá al usuario que active el botón 'Modo Admin (UAC)'. "
                    "Una vez activado, el sistema reintentará tu código con privilegios de administrador sin que tú hagas nada."
                )

                MAX_PASOS = 12
                historial_react = []
                mensaje_turno = prompt_final
                acumulado_assistant = []

                try:
                    for _ in range(MAX_PASOS):
                        if self._abortar_generacion:
                            self.ui_queue.put(("chat", "\n[JARVIS]: Proceso abortado.\n"))
                            break
                        msgs_react = []
                        # 1. Añadir historial global previo filtrado (evitar bloqueos con llamadas a funciones de la nube)
                        for m in interpreter.messages[-10:]:
                            if isinstance(m, dict):
                                r = m.get("role", "user")
                                c = m.get("content")
                                if isinstance(c, str) and c.strip():
                                    msgs_react.append({"role": r, "content": c})
                        # 2. Añadir los pasos de razonamiento de este turno
                        for role_h, cont_h in historial_react:
                            msgs_react.append({"role": role_h, "content": cont_h})
                        # 3. Inyectar el SYSTEM_LOCAL al final para que el modelo local lo tenga fresco en contexto
                        msgs_react.append({"role": "system", "content": SYSTEM_LOCAL})
                        # 4. Añadir el mensaje de usuario actual
                        msgs_react.append({"role": "user", "content": mensaje_turno})

                        payload_react = {"model": modelo_local, "messages": msgs_react, "stream": True}
                        respuesta_modelo = ""
                        stream_buffer = ""
                        in_code_block = False

                        try:
                            with requests.post("http://localhost:11434/api/chat", json=payload_react, stream=True, timeout=300) as resp:
                                for line in resp.iter_lines():
                                    if self._abortar_generacion: break
                                    if line:
                                        chunk = json.loads(line.decode("utf-8")).get("message", {}).get("content", "")
                                        if chunk:
                                            respuesta_modelo += chunk
                                            stream_buffer += chunk
                                            
                                            while True:
                                                if not in_code_block:
                                                    idx = stream_buffer.find("```")
                                                    if idx != -1:
                                                        idx_nl = stream_buffer.find("\n", idx)
                                                        if idx_nl != -1:
                                                            tag = stream_buffer[idx+3:idx_nl].strip().lower()
                                                            if tag.endswith("_run"):
                                                                text_to_print = stream_buffer[:idx]
                                                                if text_to_print:
                                                                    self.ui_queue.put(("chat_stream", text_to_print))
                                                                in_code_block = True
                                                                stream_buffer = stream_buffer[idx_nl:]
                                                            else:
                                                                text_to_print = stream_buffer[:idx_nl+1]
                                                                self.ui_queue.put(("chat_stream", text_to_print))
                                                                stream_buffer = stream_buffer[idx_nl+1:]
                                                        else:
                                                            if len(stream_buffer) > idx + 20:
                                                                text_to_print = stream_buffer[:idx+3]
                                                                self.ui_queue.put(("chat_stream", text_to_print))
                                                                stream_buffer = stream_buffer[idx+3:]
                                                            break
                                                    else:
                                                        if len(stream_buffer) > 2:
                                                            text_to_print = stream_buffer[:-2]
                                                            self.ui_queue.put(("chat_stream", text_to_print))
                                                            stream_buffer = stream_buffer[-2:]
                                                        break
                                                else:
                                                    idx = stream_buffer.find("```")
                                                    if idx != -1:
                                                        in_code_block = False
                                                        stream_buffer = stream_buffer[idx+3:]
                                                    else:
                                                        if len(stream_buffer) > 2:
                                                            stream_buffer = stream_buffer[-2:]
                                                        break
                                
                                # Al terminar el stream, imprimir lo que quede si no estamos dentro de un bloque
                                if not in_code_block and stream_buffer:
                                    self.ui_queue.put(("chat_stream", stream_buffer))
                        except Exception as ex:
                            self.ui_queue.put(("chat", f"\n[ERROR conexión] {ex}\n"))
                            break

                        self.ui_queue.put(("chat", "\n"))
                        # Limpiar marcador antes de guardar en historial (evita confusión al LLM en futuras sesiones)
                        texto_historial = respuesta_modelo.replace("[TAREA_COMPLETADA]", "").strip()
                        if texto_historial:
                            historial_react.append(("assistant", texto_historial))
                            acumulado_assistant.append(texto_historial)

                        # Extraer y ejecutar bloques de código
                        bloques = re.findall(r"```(powershell_run|python_run|cmd_run|bash_run|shell_run)\s*\n(.*?)```", respuesta_modelo, re.DOTALL | re.IGNORECASE)

                        mensaje_turno = None
                        if bloques:
                            resultados_react = []
                            for lang_b, code_b in bloques:
                                lang_b = lang_b.lower().replace("_run", "") if lang_b else "powershell"
                                code_b = code_b.strip()
                                admin_on = self.switch_admin_var.get() and lang_b != "python"
                                tag_admin = " 🔓 ADMIN" if admin_on else ""
                                self.ui_queue.put(("estado", f"Ejecutando {lang_b}{tag_admin}..."))
                                print(f"[EJECUTANDO EN LÍNEA] {lang_b}:\n{code_b}")
                                try:
                                    if lang_b == "python":
                                        res_b = subprocess.run(["python", "-c", code_b], capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
                                        salida_b = (res_b.stdout + res_b.stderr).strip() or "[Sin salida]"
                                    elif admin_on:
                                        salida_b = self.ejecutar_codigo_admin(code_b)
                                    else:
                                        res_b = subprocess.run(["powershell", "-NoProfile", "-Command", code_b], capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
                                        salida_b = (res_b.stdout + res_b.stderr).strip() or "[Sin salida]"
                                        # Auto-detección de errores de permisos → solicitar Modo Admin y reintentar
                                        _perm_keys = ["acceso denegado", "access denied", "0x80070005", "permissiondenied", "requires elevation"]
                                        if any(pk in res_b.stderr.lower() for pk in _perm_keys):
                                            self.ui_queue.put(("chat", f"\n[JARVIS] ⚠️ Error de permisos detectado: {res_b.stderr[:300]}\n"))
                                            self.ui_queue.put(("chat", "[JARVIS] 🔓 Necesito privilegios de administrador. Activa el interruptor 'Modo Admin (UAC)' en el panel lateral para que pueda reintentar.\n"))
                                            self.ui_queue.put(("hablar", "Necesito permisos de administrador. Activa el botón de Modo Admin en el panel lateral, por favor."))
                                            self._admin_granted_event.clear()
                                            if self._admin_granted_event.wait(timeout=60):
                                                self.ui_queue.put(("chat", "\n[JARVIS] ✅ Perfecto, ahora tengo permisos elevados. Reintentando el comando...\n"))
                                                self.ui_queue.put(("hablar", "Perfecto, ahora tengo permisos elevados. Reintentando."))
                                                salida_b = self.ejecutar_codigo_admin(code_b)
                                            else:
                                                self.ui_queue.put(("chat", "\n[JARVIS] ⏰ Tiempo de espera agotado esperando permisos. Continúo sin elevación.\n"))
                                    resultados_react.append(f"({lang_b}):\n{salida_b[:3000]}")
                                except subprocess.TimeoutExpired:
                                    resultados_react.append(f"({lang_b}): TIMEOUT")
                                except Exception as ex_b:
                                    resultados_react.append(f"({lang_b}): ERROR - {ex_b}")

                            mensaje_turno = "Resultados:\n" + "\n".join(resultados_react) + "\n\nAnaliza los resultados. Si la acción falló o el archivo no se encontró, debes corregir el código o buscar alternativas usando Buscar-Archivo.ps1. Si todo ha sido exitoso y la orden se cumplió al 100%, responde [TAREA_COMPLETADA]."

                        # Comprobar si se ha completado la tarea tras el bloque (solo si no se ejecutó código en este paso)
                        if "[TAREA_COMPLETADA]" in respuesta_modelo and not bloques:
                            self.ui_queue.put(("chat", "\n─────────────────────────────────\n"))
                            self.ui_queue.put(("hablar", "Listo, tarea completada."))
                            interpreter.messages.append({"role": "user", "content": prompt})
                            response_final_str = "\n".join(acumulado_assistant) if acumulado_assistant else "Listo, tarea completada."
                            interpreter.messages.append({"role": "assistant", "content": response_final_str})
                            self.ui_queue.put(("chat_final", response_final_str))
                            break
                        
                        # Si no hay bloque de código ni tarea completada, terminar
                        if not mensaje_turno:
                            self.ui_queue.put(("chat", "\n─────────────────────────────────\n"))
                            texto_limpio_react = re.sub(r'```.*?```', '', respuesta_modelo, flags=re.DOTALL).strip()
                            frases = re.split(r'(?<=[.!?])\s+', texto_limpio_react)
                            if frases and frases[0]:
                                self.ui_queue.put(("hablar", " ".join(frases[:2])[:500]))
                            interpreter.messages.append({"role": "user", "content": prompt})
                            response_final_str = "\n".join(acumulado_assistant) if acumulado_assistant else (texto_historial or "Hecho.")
                            interpreter.messages.append({"role": "assistant", "content": response_final_str})
                            self.ui_queue.put(("chat_final", response_final_str))
                            break
                    else:
                        self.ui_queue.put(("chat", "\n[JARVIS] Límite de pasos alcanzado o proceso abortado.\n"))
                        if texto_historial.strip():
                            interpreter.messages.append({"role": "user", "content": prompt})
                            response_final_str = "\n".join(acumulado_assistant) if acumulado_assistant else (texto_historial or "Límite de pasos alcanzado.")
                            interpreter.messages.append({"role": "assistant", "content": response_final_str})
                            self.ui_queue.put(("chat_final", response_final_str))

                except Exception as e_react:
                    self.ui_queue.put(("chat", f"\n[ERROR REACT] {e_react}\n"))
                # El finally externo de generar_respuesta_llm libera el lock y resetea el estado
                return

            # --- CONSENTIMIENTO PREVIO (solo para modelos de nube) ---

            # Resumen rápido de la intención (sin llamar a ningún modelo)
            palabras = prompt.strip().split()
            resumen_corto = " ".join(palabras[:10]) + ("..." if len(palabras) > 10 else "")
            resumen = f"Voy a trabajar en: {resumen_corto}"
            self.ui_queue.put(("chat", f"\n[JARVIS] Propone: {resumen}\n"))
            self.ui_queue.put(("hablar", f"{resumen}. ¿Procedo?"))
            
            consent_event = threading.Event()
            self.consent_result = False
            
            def set_consent(val):
                if not consent_event.is_set():
                    self.consent_result = val
                    consent_event.set()
                    
            self.ui_queue.put(("popup_consent", (resumen, set_consent)))
            
            def escucha_consentimiento():
                real_idx = self.get_real_mic_index()
                self.ui_queue.put(("estado", "Esperando autorización..."))
                cmd = escuchar(device_index=real_idx)
                if cmd:
                    cmd_lower = cmd.lower()
                    if any(w in cmd_lower for w in ["sí", "si", "ok", "proceder", "procede", "adelante", "dale", "hazlo", "autorizo"]):
                        set_consent(True)
                    elif any(w in cmd_lower for w in ["no", "cancela", "para", "stop", "detente", "abortar"]):
                        set_consent(False)
                    else:
                        # Respuesta no reconocida: dejar que el timeout decida (no bloquear)
                        pass
                # Si cmd es vacío (silencio), el timeout de 30s en consent_event.wait() lo resolverá
            
            threading.Thread(target=escucha_consentimiento, daemon=True).start()
            consent_event.wait(timeout=30)  # Timeout de 30s por si Ollama no responde
            if not consent_event.is_set():
                # Timeout: auto-cancelar para no quedarse colgado
                self.ui_queue.put(("chat", "\n[Timeout de autorización. Cancelado automáticamente.]\n"))
                return

            if not self.consent_result:
                self.ui_queue.put(("chat", "\n[Cancelado por el usuario]\n"))
                return
                
            self.ui_queue.put(("chat", "\n[Autorizado. Ejecutando con Auto-Run...]\n"))
            interpreter.auto_run = True
            
            # Continuamos con la lógica normal...
            self.ui_queue.put(("chat_header", f"\n[MoE] Usando cerebro: {modelo_elegido}\n[JARVIS]: "))

            response_text = ""
            for chunk in interpreter.chat(prompt_final, stream=True, display=False):
                if self._abortar_generacion:
                    self.ui_queue.put(("chat", "\n[JARVIS]: Generación en nube detenida.\n"))
                    break
                if isinstance(chunk, dict) and chunk.get("type") == "message":
                    content = chunk.get("content", "")
                    if content:
                        response_text += content
                        self.ui_queue.put(("chat_stream_final", content))
            
            self.ui_queue.put(("chat", "\n─────────────────────────────────\n"))
            if response_text:
                self.ui_queue.put(("chat_final", response_text))
                frases_cloud = re.split(r'(?<=[.!?])\s+', response_text.strip())
                self.ui_queue.put(("hablar", " ".join(frases_cloud[:2])[:500]))
            
            # Limpiar el historial de Open Interpreter de la inyección de contexto (RAG/Internet)
            if prompt_final != prompt and len(interpreter.messages) >= 2:
                for m in reversed(interpreter.messages):
                    if m.get("role") == "user" and m.get("content") == prompt_final:
                        m["content"] = prompt
                        break

        except Exception as e:
            self.ui_queue.put(("chat", f"\n[ERROR CRÍTICO] {e}\n"))
        finally:
            # Recuperar el texto final de la respuesta según el modo usado
            respuesta_final = ""
            if "response_text" in locals() and response_text.strip():
                respuesta_final = response_text.strip()
            elif "response_final_str" in locals() and response_final_str.strip():
                respuesta_final = response_final_str.strip()
            elif "texto_historial" in locals() and texto_historial.strip():
                respuesta_final = texto_historial.strip()

            # 1. Guardar memoria RAM a corto plazo (para no perder el hilo al reiniciar la app)
            try:
                with open(r"C:\JARVIS2\ram_history.json", "w", encoding="utf-8") as f:
                    json.dump(interpreter.messages, f, ensure_ascii=False, indent=4)
            except Exception:
                pass

            # 2. Guardar en Memoria Persistente Vectorial (ChromaDB) a largo plazo
            if self.switch_memoria.get() and prompt.strip() and respuesta_final:
                try:
                    import chromadb
                    from chromadb.utils import embedding_functions
                    chroma_client = chromadb.PersistentClient(path=r"C:\JARVIS2\vector_db")
                    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
                        url="http://localhost:11434/api/embeddings", 
                        model_name="nomic-embed-text"
                    )
                    collection = chroma_client.get_or_create_collection(name="jarvis_memory", embedding_function=ollama_ef)
                    doc_text = f"Usuario: {prompt}\nJARVIS: {respuesta_final}"
                    collection.add(
                        documents=[doc_text],
                        metadatas=[{"fecha": datetime.now().isoformat()}],
                        ids=[str(uuid.uuid4())]
                    )
                except Exception as ex_chroma:
                    self.ui_queue.put(("chat", f"\n[Aviso Memoria] No se pudo guardar en vector_db: {ex_chroma}\n"))
                
            self.is_generating = False
            self._prompt_lock.release()
            self.ui_queue.put(("estado", "● Listo"))

    def on_toggle_dlc(self, dlc_id):
        global config_data
        if config_data is None:
            config_data = {}
        if "dlcs" not in config_data:
            config_data["dlcs"] = {}
        if dlc_id not in config_data["dlcs"]:
            config_data["dlcs"][dlc_id] = {}
        
        if dlc_id == "memoria_vectorial":
            activo = self.switch_memoria.get()
        elif dlc_id == "youtube":
            activo = self.switch_youtube.get()
        elif dlc_id == "clicky":
            activo = self.switch_clicky.get()
        else:
            return
            
        estado_str = "activo" if activo else "inactivo"
        config_data["dlcs"][dlc_id]["estado"] = estado_str
        
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            self.ui_queue.put(("chat", f"\n[SISTEMA] Módulo '{dlc_id}' cambiado a {estado_str.upper()}.\n"))
        except Exception:
            pass

    def on_toggle_admin(self):
        """Feedback visual al activar/desactivar el Modo Administrador."""
        if self.switch_admin_var.get():
            self.ui_queue.put(("chat", "\n[SISTEMA] 🔓 Modo Administrador ACTIVADO — Los comandos PowerShell se ejecutarán con privilegios elevados (UAC).\n"))
            self._admin_granted_event.set()  # Desbloquear cualquier comando esperando permisos
        else:
            self.ui_queue.put(("chat", "\n[SISTEMA] 🔒 Modo Administrador DESACTIVADO — Ejecución estándar restaurada.\n"))
            self._admin_granted_event.clear()

    def ejecutar_codigo_admin(self, code):
        """Ejecuta código PowerShell con privilegios elevados (UAC) y retorna la salida."""
        import tempfile
        tmp_dir = tempfile.gettempdir()
        uid = uuid.uuid4().hex[:8]
        script_file = os.path.join(tmp_dir, f"jarvis_admin_{uid}.ps1")
        output_file = os.path.join(tmp_dir, f"jarvis_admin_out_{uid}.txt")
        wrapper_file = os.path.join(tmp_dir, f"jarvis_admin_wrap_{uid}.ps1")

        try:
            # Escribir código del usuario al archivo de script
            with open(script_file, "w", encoding="utf-8") as sf:
                sf.write(code)

            # Wrapper que ejecuta el script y captura toda la salida
            with open(wrapper_file, "w", encoding="utf-8") as wf:
                wf.write(f"& '{script_file}' *> '{output_file}'\n")

            # Lanzar proceso elevado (dispara UAC en pantalla del usuario)
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                 f"Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden "
                 f"-ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','{wrapper_file}')"],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace"
            )

            # Leer resultado capturado
            if os.path.exists(output_file):
                # PowerShell 5.1 '*>' redirecciona en UTF-16LE (BOM)
                with open(output_file, "r", encoding="utf-16", errors="replace") as of:
                    return of.read().strip() or "[Admin] Ejecutado correctamente (sin salida visible)."
            else:
                stderr = res.stderr.strip()
                if stderr:
                    return f"[Admin] Error o UAC denegado: {stderr}"
                return "[Admin] Ejecutado. No se capturó salida (¿UAC cancelado?)."
        except subprocess.TimeoutExpired:
            return "[Admin] TIMEOUT - El proceso elevado tardó demasiado."
        except Exception as ex:
            return f"[Admin] Error: {ex}"
        finally:
            for tmp_f in (script_file, output_file, wrapper_file):
                try:
                    os.remove(tmp_f)
                except Exception:
                    pass

    def escribir_chat(self, texto):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", texto)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def procesar_cola(self):
        try:
            while not self.ui_queue.empty():
                try:
                    tipo, valor = self.ui_queue.get_nowait()
                except queue.Empty:
                    break

                if tipo == "chat":
                    if hasattr(self, "switch_pensamiento_var") and not self.switch_pensamiento_var.get():
                        # Si está oculto el pensamiento, dejamos pasar el input del usuario, alertas de herramientas, errores o avisos UAC/Elevación
                        if any(x in valor for x in ["[Tú]:", "JARVIS-MEMORIA", "JARVIS-RED", "RUTINAS", "ERROR", "Aviso", "SISTEMA", "Timeout", "Cancelado", "Autorizado", "Elevación"]):
                            self.escribir_chat(valor)
                        continue
                    self.escribir_chat(valor)
                elif tipo == "chat_header":
                    if hasattr(self, "switch_pensamiento_var") and not self.switch_pensamiento_var.get():
                        # Si está oculto el pensamiento, solo mostramos "[JARVIS]: " para los modos de chat directo (nube o fast-track),
                        # pero no para ReAct (que mostrará todo al final con chat_final).
                        if "ReAct" not in valor:
                            self.escribir_chat("\n[JARVIS]: ")
                    else:
                        self.escribir_chat(valor)
                elif tipo == "chat_stream":
                    if hasattr(self, "switch_pensamiento_var") and not self.switch_pensamiento_var.get():
                        continue
                    self.textbox.configure(state="normal")
                    self.textbox.insert("end", valor)
                    self.textbox.configure(state="disabled")
                    self.textbox.see("end")
                elif tipo == "chat_stream_final":
                    self._current_response_streamed = True
                    self.textbox.configure(state="normal")
                    self.textbox.insert("end", valor)
                    self.textbox.configure(state="disabled")
                    self.textbox.see("end")
                elif tipo == "chat_final":
                    if hasattr(self, "switch_pensamiento_var") and not self.switch_pensamiento_var.get():
                        if not getattr(self, "_current_response_streamed", False):
                            # Limpiar bloques <think> si el modelo los produjo
                            texto_limpio = re.sub(r'<think>.*?</think>', '', valor, flags=re.DOTALL | re.IGNORECASE).strip()
                            # Eliminar todos los bloques de código markdown cerrados (```...```)
                            texto_limpio = re.sub(r'```.*?```', '', texto_limpio, flags=re.DOTALL)
                            # Eliminar bloques de código markdown que se hayan quedado abiertos al final del string por cortes en la generación
                            texto_limpio = re.sub(r'```.*$', '', texto_limpio, flags=re.DOTALL)
                            # Eliminar etiquetas internas
                            texto_limpio = texto_limpio.replace("[TAREA_COMPLETADA]", "")
                            # Normalizar saltos de línea múltiples redundantes
                            texto_limpio = re.sub(r'\n\s*\n', '\n', texto_limpio).strip()
                            
                            # Si queda vacío, mostrar un mensaje de éxito limpio
                            if not texto_limpio:
                                texto_limpio = "Listo, tarea completada."
                            self.escribir_chat(f"\n[JARVIS]: {texto_limpio}\n")
                elif tipo == "hablar":
                    # Chequeamos si el toggle de voz está activo
                    if hasattr(self, "switch_habla_var") and not self.switch_habla_var.get():
                        continue
                    # Lo lanzamos en un mini-hilo usando la función que marca is_speaking_global
                    threading.Thread(target=hablar_y_esperar, args=(valor,), daemon=True).start()

                elif tipo == "popup_consent":
                    resumen, callback = valor
                    popup = ctk.CTkToplevel(self)
                    popup.title("Requiere Autorización")
                    popup.geometry("450x250")
                    popup.attributes("-topmost", True)

                    lbl = ctk.CTkLabel(popup, text=f"JARVIS Propone:\n\n{resumen}\n\n¿Autorizas la ejecución?", wraplength=400, font=ctk.CTkFont(size=14, weight="bold"))
                    lbl.pack(pady=20)

                    # Defaults explícitos evitan bug de closure si se abren varios popups seguidos
                    def on_ok(p=popup, cb=callback):
                        p.destroy()
                        cb(True)

                    def on_cancel(p=popup, cb=callback):
                        p.destroy()
                        cb(False)

                    btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    btn_ok = ctk.CTkButton(btn_frame, text="✅ Autorizar (Voz: Sí)", command=on_ok, fg_color="green", hover_color="darkgreen")
                    btn_ok.pack(side="left", padx=20)

                    btn_cancel = ctk.CTkButton(btn_frame, text="❌ Cancelar (Voz: No)", command=on_cancel, fg_color="red", hover_color="darkred")
                    btn_cancel.pack(side="left", padx=20)

                elif tipo == "estado":
                    if hasattr(self, 'lbl_estado'):
                        v = str(valor)
                        if "Listo" in v:
                            color = "#4CAF50"   # verde
                        elif any(k in v for k in ["Trabaj", "Pens", "Creando", "Ejecut", "Buscando", "Escuchando WakeWord", "Escuchando respuesta"]):
                            color = "#FFA500"   # naranja
                        elif "Escuch" in v or "Esperando" in v:
                            color = "#42A5F5"   # azul (escuchando)
                        else:
                            color = "#888888"   # gris
                        self.lbl_estado.configure(text=v, text_color=color)

        except Exception as e_cola:
            # Nunca dejar que un fallo de UI mate el bucle de procesado
            print(f"[procesar_cola ERROR] {e_cola}")
        finally:
            self.after(100, self.procesar_cola)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
