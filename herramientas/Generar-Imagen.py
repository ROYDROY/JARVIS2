import os
import sys
import json
import base64
import requests
import argparse
from dotenv import load_dotenv

# ==============================================================================
# FIRMA ELECTRÓNICA Y LICENCIA DE USO
# SISTEMA: JARVIS 4.0 (Módulo Generación y Edición de Imágenes por API)
# PROPIEDAD INTELECTUAL DE: RUBÉN DÍAZ IGLESIAS
# CONTACTO COMERCIAL: RDIAZI@YAHOO.ES | Tlf: 616624850
# ==============================================================================

# Cargar variables de entorno desde el .env en la raíz de JARVIS2
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

def obtener_keys():
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    return gemini_key, openai_key

def obtener_mime_type(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".png": return "image/png"
    elif ext in [".jpg", ".jpeg"]: return "image/jpeg"
    elif ext == ".webp": return "image/webp"
    elif ext == ".gif": return "image/gif"
    elif ext == ".bmp": return "image/bmp"
    return "image/jpeg"

def generar_prompt_modificado(api_key, ruta_imagen, instruccion_cambio):
    """
    Envía la imagen a Gemini 1.5 Flash para que entienda el contenido
    y cree un prompt descriptivo detallado en inglés optimizado para generación,
    aplicándole el cambio solicitado por el usuario.
    """
    print(f"\n[VISIÓN GEMINI] Analizando imagen '{os.path.basename(ruta_imagen)}' para aplicar cambio...")
    try:
        with open(ruta_imagen, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] No se pudo leer la imagen de entrada: {e}")
        return None

    mime_type = obtener_mime_type(ruta_imagen)
    prompt_texto = (
        "Analyze this image and describe it in meticulous detail (composition, subjects, color palette, lighting, style). "
        f"Then, modify the scene description to incorporate the following change requested by the user: '{instruccion_cambio}'. "
        "Translate all details and compile the final modified scene into a single, cohesive, high-quality descriptive prompt in English "
        "optimized for image generation (Imagen 4 or DALL-E 3). Do NOT include any intro, explanations, or metadata. "
        "Output ONLY the final English prompt."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_texto},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": img_b64
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        response.raise_for_status()
        res_data = response.json()
        
        partes = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if partes:
            prompt_ingles = partes[0].get("text", "").strip()
            print(f"[VISIÓN GEMINI] Prompt generado con éxito para motor de imagen:\n>> {prompt_ingles}\n")
            return prompt_ingles
        else:
            print("[ERROR] La API de Gemini no devolvió texto descriptivo.")
            return None
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo al consultar a Gemini 1.5 Flash (Visión): {e}")
        return None

def generar_imagen_con_gemini(api_key, prompt_texto, ruta_salida):
    """
    Realiza la llamada a la API de Imagen 4.0 en Google AI Studio.
    """
    print(f"[IMAGEN API] Generando imagen con el prompt descriptivo usando Google Imagen 4.0...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    
    payload = {
        "instances": [
            {"prompt": prompt_texto}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=90)
        
        if response.status_code == 400:
            err_msg = response.json().get("error", {}).get("message", "")
            if "paid plans" in err_msg.lower() or "billing" in err_msg.lower():
                print("\n" + "="*80)
                print("[AVISO DE GOOGLE AI STUDIO]:")
                print("La API de Google requiere que tu cuenta tenga configurada la facturación de pago")
                print("(Pay-as-you-go / Paid Plan) para poder usar los modelos de generación de imágenes (Imagen 3/4).")
                print("El tier gratuito de Google AI Studio solo permite modelos de texto y visión de Gemini,")
                print("pero no de generación de imágenes.")
                print("\nPara solucionarlo:")
                print("1. Ve a https://aistudio.google.com/")
                print("2. Habilita la facturación (Paid plan) en tu proyecto.")
                print("3. Alternativamente, configura una clave de OpenAI (OPENAI_API_KEY) en tu .env")
                print("   para usar el modelo DALL-E 3 de forma directa.")
                print("="*80 + "\n")
                return False
                
        response.raise_for_status()
        res_data = response.json()
        
        predictions = res_data.get("predictions", [])
        if predictions:
            img_b64 = predictions[0].get("bytesBase64Encoded")
            if img_b64:
                img_data = base64.b64decode(img_b64)
                with open(ruta_salida, "wb") as f:
                    f.write(img_data)
                print(f"[IMAGEN API] ¡Éxito! Imagen guardada en: {ruta_salida}")
                return True
        print(f"[ERROR] Respuesta inesperada de la API de Google: {response.text}")
        return False
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo al invocar Google Imagen 4.0: {e}")
        return False

def generar_imagen_con_openai(api_key, prompt_texto, ruta_salida):
    """
    Realiza la llamada a la API de OpenAI (DALL-E 3) para generar la imagen.
    """
    print(f"[DALL-E API] Generando imagen con el prompt descriptivo usando OpenAI DALL-E 3...")
    url = "https://api.openai.com/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "dall-e-3",
        "prompt": prompt_texto,
        "n": 1,
        "size": "1024x1024"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        response.raise_for_status()
        res_data = response.json()
        
        img_url = res_data.get("data", [{}])[0].get("url")
        if img_url:
            print(f"[DALL-E API] Descargando imagen resultante...")
            img_res = requests.get(img_url, timeout=30)
            img_res.raise_for_status()
            with open(ruta_salida, "wb") as f:
                f.write(img_res.content)
            print(f"[DALL-E API] ¡Éxito! Imagen guardada en: {ruta_salida}")
            return True
        print(f"[ERROR] Respuesta inesperada de OpenAI: {response.text}")
        return False
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo al invocar DALL-E 3: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generador y editor de imágenes por API usando Gemini o OpenAI.")
    parser.add_argument("--prompt", type=str, required=True, help="El prompt descriptivo de la imagen o el cambio a realizar.")
    parser.add_argument("--image", type=str, default=None, help="Ruta de la imagen de entrada si se desea editar una existente.")
    parser.add_argument("--output", type=str, default=None, help="Ruta completa de salida (.png).")
    
    args = parser.parse_args()
    
    gemini_key, openai_key = obtener_keys()
    
    if not gemini_key and not openai_key:
        print("[ERROR CRÍTICO] No se encontró GEMINI_API_KEY ni OPENAI_API_KEY en tu entorno o en el archivo .env.")
        print("Configura al menos una clave de API para poder usar este generador.")
        sys.exit(1)
        
    # Definir ruta de salida por defecto en el escritorio de OneDrive
    ruta_salida = args.output
    if not ruta_salida:
        escritorio_onedrive = r"C:\Users\ROYDR\OneDrive\Desktop"
        if os.path.exists(escritorio_onedrive):
            ruta_salida = os.path.join(escritorio_onedrive, "JARVIS_imagen_generada.png")
        else:
            ruta_salida = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_imagen_generada.png")
            
    # Si viene con una imagen de entrada, usamos Gemini 1.5 Flash para generar el prompt descriptivo combinado en inglés.
    # Necesitamos una clave de Gemini para el paso de visión.
    prompt_final = args.prompt
    if args.image:
        if not os.path.isfile(args.image):
            print(f"[ERROR] El archivo de imagen original '{args.image}' no existe.")
            sys.exit(1)
        if not gemini_key:
            print("[ERROR] El análisis de imagen de entrada requiere configurar la clave de Gemini (GEMINI_API_KEY).")
            sys.exit(1)
            
        prompt_final = generar_prompt_modificado(gemini_key, args.image, args.prompt)
        if not prompt_final:
            print("[ERROR] Falló la preparación del prompt de imagen. Cancelando.")
            sys.exit(1)
            
    # Decidir motor de generación de imágenes: preferimos OpenAI (DALL-E 3) si está, sino Gemini (Imagen 4.0)
    exito = False
    if openai_key:
        exito = generar_imagen_con_openai(openai_key, prompt_final, ruta_salida)
    elif gemini_key:
        exito = generar_imagen_con_gemini(gemini_key, prompt_final, ruta_salida)
        
    if exito:
        print(f"\n[ÉXITO] Tarea completada correctamente. Archivo listo en: {ruta_salida}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
