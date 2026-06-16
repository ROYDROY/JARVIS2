import sys
import os
from interpreter import interpreter

def main():
    print("="*50)
    print(">>> INICIANDO TEST DE ESTRÉS: PILOTO LIBRE (OPCIÓN B)")
    print("="*50)
    
    try:
        sys.path.append(r"C:\JARVIS2\herramientas")
        import MotorVoz
        MotorVoz.hablar("Iniciando test de estrés con piloto web libre. Voy a programar un script para buscar quién ganó el Óscar a mejor película en 2024.")
    except:
        pass

    system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
    interpreter.system_message = system_msg
    interpreter.llm.model = "ollama/qwen2.5-coder:14b"
    interpreter.llm.context_window = 8192
    interpreter.auto_run = True

    try:
        # Le pedimos que extraiga información real de internet
        print("\n[Consultando a Qwen 14B...]")
        resultados = interpreter.chat("Escribe y ejecuta un script de python (usando requests y BeautifulSoup) para buscar en Wikipedia en español quién ganó el Óscar a Mejor Película en la ceremonia del año 2024. Extrae el título de la película y muéstralo por pantalla. No uses playwright si no es estrictamente necesario para evitar overhead. Hazlo directo y dame solo el resultado final.", display=True)
        print("\n>> RESULTADO DE LA MISIÓN:\n", resultados)
        
        try:
            import MotorVoz
            MotorVoz.hablar("Test superado con éxito. Extraí la información directamente de la web utilizando código a medida.")
        except:
            pass
            
    except Exception as e:
        print(f"\n[ERROR] El test falló: {e}")
        
    print("\n" + "="*50)
    print(">>> TEST FINALIZADO")
    print("="*50)

if __name__ == "__main__":
    main()
