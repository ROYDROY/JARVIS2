import os
import re
import json
import base64
import requests

# ==============================================================================
# FIRMA ELECTRÓNICA Y LICENCIA DE USO
# SISTEMA: JARVIS 4.0 (Módulo NervioÓptico)
# PROPIEDAD INTELECTUAL DE: RUBÉN DÍAZ IGLESIAS
# CONTACTO COMERCIAL: RDIAZI@YAHOO.ES | Tlf: 616624850
# ==============================================================================

def extraer_ruta_imagen(texto):
    """
    Busca si en el texto introducido hay una ruta a un archivo de imagen.
    Windows suele poner comillas al hacer drag & drop: "C:\ruta\imagen.png"
    Devuelve la ruta absoluta si existe y es válida, o None.
    """
    # Patrón para encontrar rutas (con o sin comillas) que terminen en extensiones de imagen
    patron = r'(?:"?([a-zA-Z]:\\[^"]+\.(?:png|jpg|jpeg|bmp|gif|webp))"?)'
    coincidencias = re.findall(patron, texto, flags=re.IGNORECASE)
    
    for ruta in coincidencias:
        ruta_limpia = ruta.strip('"')
        if os.path.isfile(ruta_limpia):
            return ruta_limpia
            
    # Intento 2: si el usuario pegó solo la ruta sin extension explícita pero es un path válido
    texto_limpio = texto.strip(' "\'')
    if os.path.isfile(texto_limpio) and any(texto_limpio.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']):
        return texto_limpio
        
    return None

def analizar_imagen_con_llava(ruta_imagen):
    """
    Envía la imagen a Llava (Ollama) para extraer una descripción detallada.
    """
    try:
        with open(ruta_imagen, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return f"[Error al leer la imagen: {e}]"

    prompt = "Describe esta imagen con el mayor nivel de detalle posible en español. Si es una captura de pantalla, lee todos los textos visibles, botones, alertas o códigos de error y descríbelos exactamente como aparecen."

    payload = {
        "model": "llava",
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }

    print("\n[NERVIO ÓPTICO] Procesando imagen con Llava (puede tardar unos segundos)...")
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        resultado = response.json()
        descripcion = resultado.get("response", "").strip()
        print("[NERVIO ÓPTICO] Imagen procesada con éxito.")
        return descripcion
    except Exception as e:
        print(f"\n[NERVIO ÓPTICO ERROR] Fallo al conectar con el modelo visual Llava: {e}")
        return None
