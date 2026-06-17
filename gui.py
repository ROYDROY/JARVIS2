import streamlit as st
import os
import sys
import json
import threading
import time
import socket
import subprocess
import ctypes
from datetime import datetime
import builtins
import streamlit.components.v1 as components
import yaml

# Intentar cargar MotorVoz
sys.path.append(r"C:\JARVIS2\herramientas")
try:
    import MotorVoz
    VOZ_DISPONIBLE = True
except:
    VOZ_DISPONIBLE = False

# Parche de seguridad absoluta: Evita que Open Interpreter bloquee Streamlit esperando confirmación
builtins.input = lambda prompt: "n"

# --- Auto-arranque de Ollama ---
def check_and_start_ollama():
    def is_port_open():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('localhost', 11434)) == 0

    if not is_port_open():
        try:
            subprocess.Popen(
                ["ollama", "serve"], 
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Esperar activamente hasta que el motor responda (max 15s)
            for _ in range(15):
                time.sleep(1)
                if is_port_open():
                    break
        except Exception as e:
            pass # Falla silenciosamente si ollama no está en el PATH

check_and_start_ollama()

# Configuración de página
st.set_page_config(page_title="JARVIS 4.0", page_icon="🤖", layout="wide")

# Ocultar botones innecesarios de Streamlit
st.markdown("""
    <style>
        .stDeployButton {display:none;}
        [data-testid="stToolbar"] {display:none;}
        #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

BASE_CONV_DIR = r"C:\JARVIS2\conversaciones"
os.makedirs(BASE_CONV_DIR, exist_ok=True)

# Inicialización de JARVIS
@st.cache_resource
def get_interpreter():
    from interpreter import interpreter
    
    # Leer config para expansiones
    modelo_cargado = "ollama/qwen2.5-coder:14b"
    config_dlcs = {}
    try:
        with open(r"C:\JARVIS2\config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if cfg and "dlcs" in cfg:
                config_dlcs = cfg["dlcs"]
                if config_dlcs.get("obliteratus", {}).get("estado") == "activo":
                    cmd = config_dlcs["obliteratus"].get("comando_instalar", "")
                    if "pull " in cmd:
                        modelo_cargado = "ollama/" + cmd.split("pull ")[1].strip()
    except:
        pass
        
    interpreter.llm.model = modelo_cargado
    interpreter.llm.api_base = "http://localhost:11434"
    interpreter.llm.context_window = 4096
    interpreter.llm.max_tokens = 2048
    interpreter.llm.supports_functions = False
    
    # Cargar contexto y SOBRESCRIBIR el veneno de Open Interpreter
    system_md_path = r"C:\JARVIS2\system.md"
    if os.path.exists(system_md_path):
        with open(system_md_path, "r", encoding="utf-8") as f:
            system_context = f.read()
            
        # Inyectar capacidades de DLCs activos dinámicamente
        if config_dlcs.get("youtube", {}).get("estado") == "activo":
            system_context += "\n- Leer YouTube (USA BLOQUE ```powershell): `C:\\JARVIS2\\venv\\Scripts\\python.exe C:\\JARVIS2\\herramientas\\Resumir-Youtube.py \"URL\"`"
            
        if config_dlcs.get("clicky", {}).get("estado") == "activo":
            system_context += "\n- Ver/Analizar imágenes y capturas de pantalla (USA BLOQUE ```powershell): `C:\\JARVIS2\\venv\\Scripts\\python.exe C:\\JARVIS2\\herramientas\\NervioOptico.py \"ruta_de_la_imagen\"`"
            
        interpreter.system_message = system_context
    
    return interpreter

jarvis = get_interpreter()
jarvis.auto_run = False  # Forzado absoluto fuera de caché

# --- GESTOR DE ESTADO ---
if "current_folder" not in st.session_state:
    st.session_state.current_folder = "General"
if "current_session_file" not in st.session_state:
    st.session_state.current_session_file = None

def get_folders():
    folders = [f for f in os.listdir(BASE_CONV_DIR) if os.path.isdir(os.path.join(BASE_CONV_DIR, f))]
    if "General" not in folders:
        os.makedirs(os.path.join(BASE_CONV_DIR, "General"), exist_ok=True)
        folders.append("General")
    return sorted(folders)

def get_sessions(folder):
    folder_path = os.path.join(BASE_CONV_DIR, folder)
    if not os.path.exists(folder_path): return []
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    return sorted(files, reverse=True)

def save_session():
    if not st.session_state.current_session_file:
        return
    with open(st.session_state.current_session_file, "w", encoding="utf-8") as f:
        json.dump(jarvis.messages, f, ensure_ascii=False, indent=4)

def load_session(file_path):
    st.session_state.current_session_file = file_path
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                jarvis.messages = json.load(f)
            except:
                jarvis.messages = []
    else:
        jarvis.messages = []

def new_session():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"Sesion_{timestamp}.json"
    st.session_state.current_session_file = os.path.join(BASE_CONV_DIR, st.session_state.current_folder, file_name)
    jarvis.messages = []
    save_session()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Tus Carpetas")
    
    folders = get_folders()
    idx = folders.index(st.session_state.current_folder) if st.session_state.current_folder in folders else 0
    selected_folder = st.selectbox("Carpeta actual:", folders, index=idx)
    
    if selected_folder != st.session_state.current_folder:
        st.session_state.current_folder = selected_folder
        st.session_state.current_session_file = None
        st.rerun()

    with st.expander("➕ Nueva Carpeta"):
        new_folder_name = st.text_input("Nombre de la carpeta:")
        if st.button("Crear"):
            if new_folder_name:
                os.makedirs(os.path.join(BASE_CONV_DIR, new_folder_name), exist_ok=True)
                st.session_state.current_folder = new_folder_name
                st.session_state.current_session_file = None
                st.rerun()
                
    st.divider()
    st.header("💬 Conversaciones")
    
    if st.button("➕ Nueva Conversación", use_container_width=True):
        new_session()
        st.rerun()
        
    sessions = get_sessions(st.session_state.current_folder)
    
    # Autocargar la más reciente si no hay ninguna seleccionada
    if not st.session_state.current_session_file and sessions:
        load_session(os.path.join(BASE_CONV_DIR, st.session_state.current_folder, sessions[0]))
    elif not st.session_state.current_session_file and not sessions:
        new_session()
        sessions = get_sessions(st.session_state.current_folder)
        
    current_file_basename = os.path.basename(st.session_state.current_session_file) if st.session_state.current_session_file else None
    
    s_idx = sessions.index(current_file_basename) if current_file_basename in sessions else 0
    selected_session = st.selectbox("Historial:", sessions, index=s_idx)
    
    if selected_session and selected_session != current_file_basename:
        load_session(os.path.join(BASE_CONV_DIR, st.session_state.current_folder, selected_session))
        st.rerun()

    if st.button("🗑️ Borrar Conversación Actual"):
        if st.session_state.current_session_file and os.path.exists(st.session_state.current_session_file):
            os.remove(st.session_state.current_session_file)
            st.session_state.current_session_file = None
            jarvis.messages = []
            st.rerun()

    st.divider()
    st.header("📎 Archivos y Fotos")
    uploaded_files = st.file_uploader("Arrastra aquí tus archivos", accept_multiple_files=True)
    if uploaded_files:
        sandbox_dir = r"C:\JARVIS2\sandbox"
        os.makedirs(sandbox_dir, exist_ok=True)
        paths = []
        for uf in uploaded_files:
            file_path = os.path.join(sandbox_dir, uf.name)
            with open(file_path, "wb") as f:
                f.write(uf.getbuffer())
            paths.append(file_path)
            
        if st.button("Enviar archivos a JARVIS"):
            files_msg = "El usuario acaba de subir los siguientes archivos a tu carpeta sandbox:\n" + "\n".join(paths) + "\nPor favor, confírmale que los tienes listos para analizar."
            with st.spinner("Analizando archivos..."):
                try:
                    jarvis.chat(files_msg, display=False)
                except Exception as e:
                    error_msg = f"JARVIS no ha podido conectar con Ollama. El cerebro local está inalcanzable.\nDetalles: {e}"
                    st.error(f"⚠️ **Error de conexión crítico:** {error_msg}")
                    if os.name == 'nt':
                        ctypes.windll.user32.MessageBoxW(0, error_msg, "Error Crítico de JARVIS", 0x10)
                save_session()
                st.rerun()

    st.divider()
    
    # --- GESTOR DE EXPANSIONES ---
    st.header("🧩 Gestor de Expansiones")
    try:
        with open(r"C:\JARVIS2\config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except:
        config = {}
        
    if "dlcs" in config:
        for dlc_id, dlc_data in config["dlcs"].items():
            with st.expander(f"{'🟢' if dlc_data.get('estado') == 'activo' else '⚪'} {dlc_data.get('nombre', dlc_id)}"):
                st.caption(dlc_data.get('descripcion', ''))
                
                estado_actual = dlc_data.get('estado', 'inactivo')
                
                if estado_actual == "inactivo":
                    if st.button(f"⬇️ Instalar y Activar", key=f"instalar_{dlc_id}", use_container_width=True):
                        with st.spinner(f"Instalando {dlc_data.get('nombre')} en segundo plano..."):
                            cmd = dlc_data.get('comando_instalar')
                            if cmd:
                                subprocess.run(cmd, shell=True)
                            config['dlcs'][dlc_id]['estado'] = 'activo'
                            with open(r"C:\JARVIS2\config.yaml", "w", encoding="utf-8") as f:
                                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                            st.rerun()
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"⏸️ Apagar", key=f"apagar_{dlc_id}", use_container_width=True):
                            config['dlcs'][dlc_id]['estado'] = 'inactivo'
                            with open(r"C:\JARVIS2\config.yaml", "w", encoding="utf-8") as f:
                                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                            st.cache_resource.clear() # Limpiar cache para recargar el modelo si cambia
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ Purgar", key=f"purgar_{dlc_id}", use_container_width=True):
                            with st.spinner(f"Desinstalando y borrando datos..."):
                                cmd = dlc_data.get('comando_desinstalar')
                                if cmd:
                                    subprocess.run(cmd, shell=True)
                                config['dlcs'][dlc_id]['estado'] = 'inactivo'
                                with open(r"C:\JARVIS2\config.yaml", "w", encoding="utf-8") as f:
                                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                                st.cache_resource.clear()
                                st.rerun()
                                
    st.divider()
    st.header("🎙️ Control de Voz")
    
    prompt_voz = None
    if VOZ_DISPONIBLE:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        
        # Leer el micro seleccionado previamente
        try:
            with open(r"C:\JARVIS2\config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                idx_guardado = cfg.get("mic_index", 0) if cfg else 0
        except:
            idx_guardado = 0
            cfg = {}
            
        if idx_guardado >= len(mics): idx_guardado = 0
        
        selected_mic = st.selectbox("Seleccionar Micrófono", mics, index=idx_guardado)
        selected_index = mics.index(selected_mic)
        
        # Guardar si cambia
        if selected_index != idx_guardado:
            if not cfg: cfg = {}
            cfg["mic_index"] = selected_index
            with open(r"C:\JARVIS2\config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
                
        usar_voz_respuesta = st.toggle("🔊 Leer respuestas en voz alta", value=True)
        
        if st.button("🎤 Hablar por Micrófono", use_container_width=True):
            with st.spinner("Escuchando... Habla ahora."):
                MotorVoz.hablar("Te escucho")
                texto = MotorVoz.escuchar(device_index=selected_index)
                if texto:
                    prompt_voz = texto
                    st.success(f"Te he entendido: {texto}")
                else:
                    st.warning("No he captado nada.")

    st.divider()
    if st.button("🛑 Apagar JARVIS (Cerrar Motor)", use_container_width=True):
        save_session()
        
        # Inject Javascript to try to close the tab, or at least redirect to about:blank to avoid the connection error
        # Inyectar Javascript para redirigir la pestaña principal a una página en blanco
        # Esto descarga la interfaz de Streamlit ANTES de que muera el servidor, evitando el popup.
        components.html(
            """
            <script>
                window.parent.document.body.innerHTML = "<h1 style='color:white; text-align:center; margin-top:20%; font-family:sans-serif;'>JARVIS apagado. Ya puedes cerrar la pestaña.</h1>";
            </script>
            """, height=0
        )
        
        # Matamos el servidor 2 segundos después
        def kill_server():
            time.sleep(2)
            os._exit(0)
            
        threading.Thread(target=kill_server).start()

# --- MAIN UI ---
st.title("🤖 JARVIS 4.0")
st.markdown("Bienvenido a la interfaz gráfica de tu asistente local seguro (Versión 4.0).")

chat_container = st.container()

with chat_container:
    for msg in jarvis.messages:
        if msg.get("role") == "system":
            continue
            
        with st.chat_message(msg.get("role", "assistant")):
            if msg.get("type") == "message" and "content" in msg:
                st.markdown(msg["content"])
            elif msg.get("type") == "code":
                code = msg.get("content", "")
                st.code(code)
                
                # Si el código no ha sido ejecutado (no hay consola debajo), mostramos botón
                idx = jarvis.messages.index(msg)
                ha_sido_ejecutado = False
                if idx < len(jarvis.messages) - 1:
                    next_msg = jarvis.messages[idx+1]
                    if next_msg.get("role") == "computer" and next_msg.get("type") == "console":
                        ha_sido_ejecutado = True
                        
                if not ha_sido_ejecutado:
                    if st.button("▶️ Autorizar y Ejecutar", key=f"run_code_{idx}"):
                        with st.spinner("Ejecutando de forma segura..."):
                            formato = msg.get("format", "powershell")
                            if formato == "powershell" or formato == "shell":
                                result = subprocess.run(["powershell.exe", "-Command", code], capture_output=True, text=True)
                                output = result.stdout + result.stderr
                            elif formato == "python":
                                with open("temp_exec.py", "w", encoding="utf-8") as f:
                                    f.write(code)
                                result = subprocess.run([sys.executable, "temp_exec.py"], capture_output=True, text=True)
                                output = result.stdout + result.stderr
                            else:
                                output = f"Formato no soportado: {formato}"
                            
                            if not output.strip():
                                output = "Ejecución completada con éxito (sin salida)."
                                
                            # Añadir el resultado al historial de JARVIS
                            jarvis.messages.append({
                                "role": "computer",
                                "type": "console",
                                "format": "output",
                                "content": output
                            })
                            save_session()
                            
                            # Avisar a JARVIS de que ya hemos ejecutado su código y pasarle el output
                            jarvis.chat("He ejecutado tu código. Esta es la salida:\n" + output, display=False)
                            save_session()
                            st.rerun()

            elif msg.get("type") == "console":
                out = msg.get("content", "")
                if out:
                    with st.expander("Salida del terminal"):
                        st.code(out)

prompt_teclado = st.chat_input("Pídele algo a JARVIS...")
prompt_final = prompt_voz if prompt_voz else prompt_teclado

if prompt_final:
    with st.chat_message("user"):
        st.markdown(prompt_final)
        
    with st.chat_message("assistant"):
        with st.spinner("JARVIS está pensando..."):
            try:
                # Contamos mensajes previos para saber qué ha añadido nuevo
                num_mensajes_previos = len(jarvis.messages)
                
                jarvis.chat(prompt_final, display=False)
                
                # Extraemos la respuesta para leerla en voz alta si está activo el toggle
                if VOZ_DISPONIBLE and usar_voz_respuesta:
                    nuevos_mensajes = jarvis.messages[num_mensajes_previos:]
                    respuestas_texto = [m["content"] for m in nuevos_mensajes if m.get("role") == "assistant" and m.get("type") == "message" and "content" in m]
                    if respuestas_texto:
                        # Leer la última o la unión de ellas
                        texto_a_leer = " ".join(respuestas_texto)
                        # Limpiamos bloques de código para que no lea barbaridades
                        import re
                        texto_limpio = re.sub(r'```.*?```', ' bloque de código omitido ', texto_a_leer, flags=re.DOTALL)
                        MotorVoz.hablar(texto_limpio)
                        
            except Exception as e:
                error_msg = f"JARVIS no ha podido conectar con Ollama. Asegúrate de que el motor local está corriendo.\nDetalles: {e}"
                st.error(f"⚠️ **Error de conexión crítico:** {error_msg}")
                if os.name == 'nt':
                    ctypes.windll.user32.MessageBoxW(0, error_msg, "Error Crítico de JARVIS", 0x10)
            save_session()
            st.rerun()
