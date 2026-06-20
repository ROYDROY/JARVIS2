import os
import json
import urllib.request
import re
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(ROOT, "logs", "sesion_actual.log")
MEMORIA_PATH = os.path.join(ROOT, "memoria", "memoria.json")

# Cargar Configuración Dinámica
try:
    with open(os.path.join(ROOT, "config.yaml"), "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
except:
    config = {}

# Modelo dinámico (Soporte para OBLITERATUS)
MODEL = "qwen2.5:7b-instruct-q5_K_M"
if config.get("dlcs", {}).get("obliteratus", {}).get("estado") == "activo":
    cmd = config["dlcs"]["obliteratus"].get("comando_instalar", "")
    if "pull " in cmd:
        MODEL = cmd.split("pull ")[1].strip()

# Inicializar modelo vectorial si el DLC está activo
vector_activo = config.get("dlcs", {}).get("memoria_vectorial", {}).get("estado") == "activo"
vector_model = None
if vector_activo:
    try:
        from sentence_transformers import SentenceTransformer
        print("[Memoria] Cargando motor vectorial (Claude-Mem)...")
        vector_model = SentenceTransformer('all-MiniLM-L6-v2')
    except ImportError:
        print("[Memoria] Error: DLC Memoria Vectorial activo pero falta la librería. Usa la interfaz para instalarlo.")
        vector_activo = False

def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()
    except Exception as e:
        print(f"  [Error Ollama] {e}")
        return ""

def extract_json(text):
    # Intentar limpiar la respuesta de ollama para extraer solo el JSON
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except Exception:
        return None

def main():
    if not os.path.exists(LOG_PATH):
        return  # Si no hay log, no hay sesión previa. Salir limpio.
        
    print("[Memoria] Procesando sesion anterior...")
    
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        log_content = f.read()
        
    # Llamada 1: Datos base
    prompt_base = f"Resume esta sesion en JSON con exactamente estos campos: fecha (string con fecha actual en formato YYYY-MM-DD), temas (array de strings), decisiones (array de strings), archivos_modificados (array de strings). Devuelve UNICAMENTE el JSON, sin explicaciones, sin markdown, sin bloques de codigo. Sesion: {log_content}"
    resp_base = call_ollama(prompt_base)
    json_base = extract_json(resp_base)
    
    if not json_base:
        print("  AVISO — La IA no devolvió un JSON válido para los datos base.")
        return
        
    # Llamada 2: Hechos (Aislada para saltarse la limitación del LLM)
    prompt_hechos = f"Extrae datos concretos del usuario o sistema de este log. Responde solo con JSON: {{\"hechos\":[\"dato\"]}}. Array vacio si no hay datos concretos: {{\"hechos\":[]}}. Devuelve UNICAMENTE el JSON puro, sin explicaciones. Sesion: {log_content}"
    resp_hechos = call_ollama(prompt_hechos)
    json_hechos = extract_json(resp_hechos)
    
    hechos_array = []
    if json_hechos and "hechos" in json_hechos:
        hechos_array = json_hechos["hechos"]
        
    # Construir objeto final
    sesion = {
        "fecha": json_base.get("fecha", ""),
        "temas": json_base.get("temas", []),
        "decisiones": json_base.get("decisiones", []),
        "archivos_modificados": json_base.get("archivos_modificados", []),
        "hechos": hechos_array
    }
    
    # Validar que tenga contenido útil
    tiene_contenido = (
        len(sesion["temas"]) > 0 or 
        len(sesion["decisiones"]) > 0 or 
        len(sesion["archivos_modificados"]) > 0 or 
        len(sesion["hechos"]) > 0
    )
    
    if tiene_contenido:
        if os.path.exists(MEMORIA_PATH):
            with open(MEMORIA_PATH, 'r', encoding='utf-8') as f:
                try:
                    memoria = json.load(f)
                except Exception:
                    memoria = {"hechos": [], "sesiones": []}
        else:
            memoria = {"hechos": [], "sesiones": []}
            
        if "sesiones" not in memoria:
            memoria["sesiones"] = []
            
        # Generar vector matemático si está activo
        if vector_activo and vector_model:
            texto_sesion = f"Temas: {', '.join(sesion['temas'])}. Decisiones: {', '.join(sesion['decisiones'])}. Hechos: {', '.join(sesion['hechos'])}."
            try:
                sesion["vector"] = vector_model.encode(texto_sesion).tolist()
                print("  OK — Vector matemático generado")
            except Exception as e:
                print(f"  Error generando vector: {e}")
                
        memoria["sesiones"].append(sesion)
        
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(memoria, f, indent=4, ensure_ascii=False)
            
        print("  OK — sesion registrada")
    else:
        print("  AVISO — sesion sin contenido util, no registrada")
        
    # Borrar log para no procesarlo 2 veces
    try:
        os.remove(LOG_PATH)
    except Exception:
        pass

if __name__ == "__main__":
    main()
