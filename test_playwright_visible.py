import sys
import os
from interpreter import interpreter

def main():
    print("="*60)
    print(">>> TEST: NAVEGACIÓN WEB A LA VISTA (PLAYWRIGHT)")
    print("="*60)
    
    try:
        sys.path.append(r"C:\JARVIS2\herramientas")
        import MotorVoz
        MotorVoz.hablar("Iniciando prueba de navegación visible. Voy a tomar el control del navegador para hacer una búsqueda en Google delante de ti.")
    except:
        pass

    system_msg = open(r"C:\JARVIS2\system.md", "r", encoding="utf-8-sig").read()
    interpreter.system_message = system_msg
    interpreter.llm.model = "ollama/qwen2.5-coder:14b"
    interpreter.llm.context_window = 8192
    interpreter.auto_run = True

    try:
        # Petición explícita para que se "ponga a la vista" y use Playwright
        peticion = "Ponte a la vista. Abre google, busca 'antigravedad', haz click en buscar y dime el título del primer resultado. Usa playwright."
        print(f"\n[Usuario]: {peticion}")
        print("\n[Consultando a Qwen 14B...]")
        
        resultados = interpreter.chat(peticion, display=True)
        print("\n>> RESULTADO DE LA MISIÓN:\n", resultados)
        
        try:
            MotorVoz.hablar("Navegación visible completada. Prueba superada.")
        except:
            pass
            
    except Exception as e:
        print(f"\n[ERROR] El test falló: {e}")
        
    print("\n" + "="*60)
    print(">>> TEST FINALIZADO")
    print("="*60)

if __name__ == "__main__":
    main()
