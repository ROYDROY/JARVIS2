import sys
import os
import subprocess
from litellm import completion

def main():
    # Git pasa varios argumentos al hook prepare-commit-msg
    # sys.argv[1]: Ruta al archivo que contiene el mensaje del commit
    # sys.argv[2]: Fuente del mensaje (message, template, merge, squash, commit). Puede estar vacío.
    
    commit_msg_filepath = sys.argv[1]
    
    # Si el usuario ya ha escrito un mensaje a mano (ej: git commit -m "mi mensaje"), no hacemos nada.
    if len(sys.argv) > 2 and sys.argv[2] in ["message", "merge"]:
        return

    # Sacamos los cambios que están "en la zona de preparación" (los que van a entrar en el commit)
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], encoding="utf-8")
    except Exception as e:
        print(f"Error obteniendo el diff: {e}")
        return

    if not diff.strip():
        return # No hay cambios

    print("\n[JARVIS] Leyendo tus cambios para escribir el mensaje del commit...")

    # Le pedimos a Ollama que resuma los cambios
    prompt = f"""
Eres JARVIS. El usuario está haciendo un 'commit' en su repositorio de código local.
Aquí tienes el 'git diff' (los cambios realizados):

{diff[:3000]} # Limitamos a 3000 caracteres por si es muy largo

Tu tarea: Escribe un mensaje de commit corto, directo y pragmático. 
Solo el mensaje, nada de saludos ni explicaciones.
Formato ideal:
1 linea de resumen.
- Punto clave 1
- Punto clave 2
"""
    try:
        response = completion(
            model="ollama/qwen2.5:7b-instruct-q5_K_M",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:11434"
        )
        ai_message = response.choices[0].message.content.strip()
        
        # Leemos el archivo original (que puede tener instrucciones comentadas de Git)
        with open(commit_msg_filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Sobrescribimos el archivo con el mensaje de la IA arriba del todo
        with open(commit_msg_filepath, 'w', encoding='utf-8') as f:
            f.write(ai_message + "\n\n" + original_content)
            
        print("[JARVIS] ¡Mensaje escrito! Continúa con tu commit.\n")
        
    except Exception as e:
        print(f"[JARVIS] No pude conectar con Ollama para el commit automático. Escríbelo a mano. (Error: {e})")

if __name__ == "__main__":
    main()
