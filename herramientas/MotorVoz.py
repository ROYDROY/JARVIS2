import subprocess
import os
import time
import re
import speech_recognition as sr
import uuid

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
pygame.mixer.init()

# ==============================================================================
# FIRMA ELECTRÓNICA Y LICENCIA DE USO
# SISTEMA: JARVIS 4.0 (Módulo VibeVoice)
# PROPIEDAD INTELECTUAL DE: RUBÉN DÍAZ IGLESIAS
# CONTACTO COMERCIAL: RDIAZI@YAHOO.ES | Tlf: 616624850
# ==============================================================================

def limpiar_texto(texto):
    """Limpia el texto de caracteres especiales y markdown para hablar."""
    # Eliminar bloques de código
    texto = re.sub(r'```.*?```', ' bloque de código omitido ', texto, flags=re.DOTALL)
    # Eliminar símbolos molestos
    texto = re.sub(r'[*`_~]', '', texto)
    return texto.strip()

def hablar(texto):
    """Convierte texto a voz y lo reproduce usando Edge-TTS (Alvaro)"""
    texto = limpiar_texto(texto)
    texto = re.sub(r'[\{\}\[\]]', '', texto) # Limpiar llaves vacías JSON
    if len(texto.strip()) < 2:
        return
        
    import uuid
    mp3_path = os.path.join(os.path.dirname(__file__), f"temp_voice_{uuid.uuid4().hex}.mp3")
    
    # Usar voz de España (AlvaroNeural o ElviraNeural)
    cmd = [
        r"C:\JARVIS2\venv\Scripts\edge-tts.exe", 
        "--voice", "es-ES-AlvaroNeural", 
        "--text", texto, 
        "--write-media", mp3_path
    ]
    
    # Ejecutar edge-tts de forma silenciosa
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Comprobar que el archivo existe y no está corrupto/vacío
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
        try:
            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[VOZ ERROR] Pygame falló: {e}")
        finally:
            # Limpiar archivo temporal (aunque falle)
            try:
                os.remove(mp3_path)
            except:
                pass

def escuchar_pasivo(device_index=None):
    """Escucha en segundo plano buscando la palabra mágica"""
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=device_index) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            # Escucha corta y rápida para no bloquear
            audio = r.listen(source, timeout=1, phrase_time_limit=3)
            texto = r.recognize_google(audio, language="es-ES").lower()
            if "jarvis" in texto or "computadora" in texto:
                return True
            return False
    except:
        return False

def escuchar(device_index=None):
    """Escucha el micrófono y lo convierte a texto"""
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=device_index) as source:
            print("\r[OÍDO] Te escucho...      ", end="", flush=True)
            audio = r.listen(source, timeout=5, phrase_time_limit=15)
            texto = r.recognize_google(audio, language="es-ES")
            print(f"\r[OÍDO] Has dicho: '{texto}'")
            return texto
    except sr.WaitTimeoutError:
        print("\r" + " "*30 + "\r", end="") # Limpiar línea
        return ""
    except sr.UnknownValueError:
        print("\r[OÍDO] No te he entendido.", end="")
        time.sleep(1)
        print("\r" + " "*40 + "\r", end="")
        return ""
    except Exception as e:
        print(f"\r[OÍDO ERROR] {e}")
        return ""

if __name__ == "__main__":
    print("Probando módulo de voz...")
    hablar("Sistemas vocales en línea. Hola Rubén.")
    print("Módulo de voz probado.")
