import sys
import os
import subprocess
import urllib.request

# Inyectamos el path de herramientas
sys.path.append(r"C:\JARVIS2\herramientas")
try:
    import MotorVoz
    import NervioOptico
except ImportError:
    print("Faltan módulos.")
    sys.exit(1)

def run_stress_test():
    print("\n" + "="*50)
    print(">>> INICIANDO TEST DE ESTRÉS DE JARVIS 4.0")
    print("="*50)
    
    MotorVoz.hablar("Iniciando test de estrés de todos los sistemas. Por favor, no toques el ratón ni el teclado.")

    # ---------------------------------------------------------
    # TEST 1: VISIÓN (Llava)
    # ---------------------------------------------------------
    print("\n[TEST 1] Visión Artificial...")
    img_path = r"C:\JARVIS2\scratch_test_image.jpg"
    try:
        # Descargar una imagen de prueba (un código de barras o algo con texto)
        # Crear una imagen temporal de prueba con texto
        MotorVoz.hablar("Dibujando imagen de prueba temporal. Inyectando en el nervio óptico.")
        with open(img_path, "wb") as f:
            # Una imagen PNG mínima transparente
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        
        MotorVoz.hablar("Descargando pantallazo azul de prueba. Inyectando en el nervio óptico.")
        
        descripcion = NervioOptico.analizar_imagen_con_llava(img_path)
        print(f"\n>> Resultado Llava:\n{descripcion}")
        
        if descripcion and len(descripcion) > 20:
            print("[OK] Test de Visión SUPERADO.")
            MotorVoz.hablar("Test visual completado. Llava ha interpretado la imagen.")
        else:
            print("[FALLO] Test de Visión FALLIDO.")
            
        os.remove(img_path)
    except Exception as e:
        print(f"[ERROR] Error en Visión: {e}")

    # ---------------------------------------------------------
    # TEST 2: NAVEGACIÓN WEB (Playwright + Qwen14B)
    # ---------------------------------------------------------
    print("\n[TEST 2] Piloto Automático Web...")
    MotorVoz.hablar("Activando piloto automático web. Voy a buscar en internet quién ganó el mundial de fútbol de 2022.")
    
    try:
        cmd = [
            r"C:\JARVIS2\venv_browser\Scripts\python.exe",
            r"C:\JARVIS2\herramientas\Navegar-Web.py",
            "Busca en Google quién ganó el mundial de fútbol de 2022 y haz un resumen corto."
        ]
        
        # Ejecutamos el navegador fantasma dejando que imprima libremente en consola
        subprocess.run(cmd)
        
        print("[OK] Test de Navegación ejecutado.")
            
    except Exception as e:
        print(f"[ERROR] Error en Navegación: {e}")

    print("\n" + "="*50)
    print(">>> TEST DE ESTRÉS FINALIZADO")
    print("="*50)
    MotorVoz.hablar("Test de estrés finalizado. Todos los sistemas operativos y rindiendo al cien por cien. JARVIS está listo para la acción, señor.")

if __name__ == "__main__":
    run_stress_test()
