import sys
import os
import json
import re
import subprocess

def main():
    print("="*60)
    print(">>> TEST: NAVEGACIÓN WEB RÁPIDA (SCRAPING INVISIBLE)")
    print("="*60)
    
    sys.path.append(r"C:\JARVIS2\herramientas")
    try:
        import MotorVoz
        MotorVoz.hablar("Probando el modo de rastreo invisible. Extrayendo datos de Wikipedia en tres, dos, uno.")
    except:
        pass

    from interpreter import interpreter
    system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
    interpreter.system_message = system_msg
    interpreter.llm.model = "ollama/qwen2.5-coder:14b"
    interpreter.llm.context_window = 8192
    
    # Hacemos la consulta
    peticion = "Busca en la Wikipedia en español quién ganó el Óscar a mejor película en el año 2024. Escribe el script en Python usando BeautifulSoup y urllib o requests. Extrae solo el título de la película y haz un print."
    
    print("\n[Consultando a Qwen 14B...]")
    response_text = ""
    for chunk in interpreter.chat(peticion, stream=True, display=False):
        if isinstance(chunk, dict) and chunk.get("type") == "message":
            response_text += chunk.get("content", "")

    # Aplicamos el mismo parche de autocuración que tiene launcher.py
    if '"name": "execute"' in response_text and '"code":' in response_text:
        try:
            inicio = response_text.find('{')
            fin = response_text.rfind('}')
            if inicio != -1 and fin != -1:
                json_str = response_text[inicio:fin+1]
                datos = json.loads(json_str)
                if datos.get("name") == "execute":
                    code = datos["arguments"]["code"]
                    code = re.sub(r'```[a-zA-Z]*\n', '', code)
                    code = code.replace('```', '').strip()
                    
                    print(f"\n[Ejecutando script rastreador...]\n")
                    resultado = subprocess.run(["python", "-c", code], capture_output=True, text=True, encoding='utf-8')
                    
                    dato_extraido = resultado.stdout.strip()
                    print(f">> DATO EXTRAÍDO DE LA WEB: {dato_extraido}")
                    
                    if dato_extraido:
                        try:
                            # Que lo lea en voz alta simulando la interacción final
                            MotorVoz.hablar(f"Hecho. La información extraída de la red es la siguiente: {dato_extraido}")
                        except:
                            pass
        except Exception as e:
            print(f"\n[ERROR de ejecución] {e}")

    print("\n" + "="*60)
    print(">>> TEST FINALIZADO")
    print("="*60)

if __name__ == "__main__":
    main()
