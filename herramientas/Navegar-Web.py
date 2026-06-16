import sys
import asyncio
from langchain_ollama import ChatOllama
from browser_use import Agent

# Parche de compatibilidad interna para browser-use
ChatOllama.provider = "ollama"
ChatOllama.model_name = "qwen2.5-coder:14b"

async def main():
    if len(sys.argv) < 2:
        print("Uso: python Navegar-Web.py \"Instrucción para navegar\"")
        return
        
    tarea = sys.argv[1]
    print(f"=== JARVIS AUTO-NAVEGADOR ===")
    print(f"Tarea recibida: {tarea}")
    
    # Conectamos con el cerebro local (Qwen2.5) pero le damos memoria extendida (32K) 
    # para que sea capaz de leer todo el código de la web sin asfixiarse.
    llm = ChatOllama(
        model="qwen2.5-coder:14b",
        base_url="http://localhost:11434",
        num_ctx=32000
    )
    
    print("[JARVIS] Levantando navegador fantasma y procesando web...")
    try:
        agent = Agent(
            task=tarea,
            llm=llm
        )
        result = await agent.run()
        print("\n=== REPORTE DE NAVEGACIÓN ===")
        print(result.final_result())
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] La navegación falló: {e}")

if __name__ == "__main__":
    asyncio.run(main())
