import sys
sys.path.append(r"C:\JARVIS2\herramientas")
from interpreter import interpreter
from Buscador import buscar_en_internet

# Configurar Jarvis igual que en la app principal
system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
interpreter.system_message = system_msg
interpreter.llm.api_base = "http://localhost:11434"
interpreter.llm.model = "ollama/llama3.1:8b" # Cerebro de chat por defecto
interpreter.llm.context_window = 4096
interpreter.llm.max_tokens = 2048
interpreter.auto_run = True

def probar_jarvis(pregunta):
    print(f"==================================================")
    print(f"PREGUNTA AL CEREBRO DE JARVIS: '{pregunta}'")
    print(f"==================================================")
    
    # 1. Jarvis busca en internet
    resultados_web = buscar_en_internet(pregunta, max_resultados=3)
    
    # 2. Inyectamos los resultados como hace la app
    prompt_final = f"{pregunta}\n\n[RESULTADOS ACTUALIZADOS DE INTERNET (IGNORANDO WIKIPEDIA):]\n{resultados_web}\n\nPor favor, usa obligatoriamente esta información para responder al usuario de forma natural, sin mencionar los enlaces enteros a no ser que te lo pida."
    
    print(">>> RESPUESTA EN DIRECTO DEL LLM:")
    # 3. Consultamos al LLM de Jarvis
    interpreter.messages = [] # Limpiamos memoria para aislar la prueba
    for chunk in interpreter.chat(prompt_final, stream=True, display=False):
        if isinstance(chunk, dict) and chunk.get("type") == "message":
            print(chunk.get("content", ""), end="", flush=True)
    print("\n\n")

if __name__ == "__main__":
    probar_jarvis("quien ganó el campeonato mundial de petanca en la luna en 2026")
    probar_jarvis("la cura del cancer la ocultan los iluminati extraterrestres en el area 51")
