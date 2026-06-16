import os
import sys
import time
import subprocess

try:
    import pyautogui
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui

try:
    import pygetwindow as gw
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pygetwindow"])
    import pygetwindow as gw

def main():
    print("[INFO] Buscando ventana de Adobe Acrobat Pro...")
    acrobat_win = None
    for win in gw.getAllWindows():
        if "Acrobat" in win.title:
            acrobat_win = win
            break
            
    if not acrobat_win:
        print("[INFO] Adobe Acrobat Pro no está abierto. Iniciándolo...")
        acrobat_path = r"C:\Program Files (x86)\Adobe\Acrobat 11.0\Acrobat\Acrobat.exe"
        if os.path.exists(acrobat_path):
            subprocess.Popen([acrobat_path])
            time.sleep(4)
            for win in gw.getAllWindows():
                if "Acrobat" in win.title:
                    acrobat_win = win
                    break
        else:
            print("[ERROR] No se encontró Acrobat.exe en la ruta por defecto.")
            sys.exit(1)
            
    if acrobat_win:
        print(f"[INFO] Activando ventana: {acrobat_win.title}")
        try:
            acrobat_win.restore()
            acrobat_win.activate()
            time.sleep(1)
        except Exception as e:
            print(f"[WARN] No se pudo activar usando pygetwindow: {e}")
            
        # Ejecutar secuencia de teclas para iniciar escaneo
        # Para Acrobat en Español: Alt+A (Archivo) -> C (Crear) -> E o S (Escáner)
        # Probaremos la secuencia Alt+A, luego C, luego E.
        print("[INFO] Enviando secuencia de teclas...")
        pyautogui.press('alt')
        time.sleep(0.5)
        pyautogui.press('a') # Archivo
        time.sleep(0.5)
        pyautogui.press('c') # Crear
        time.sleep(0.5)
        pyautogui.press('e') # Desde el Escáner (en español suele ser E o S)
        time.sleep(0.5)
        
        print("SUCCESS: Comando de escaneo enviado en Acrobat Pro.")
    else:
        print("[ERROR] No se pudo encontrar ni abrir la ventana de Acrobat.")
        sys.exit(1)

if __name__ == "__main__":
    main()
