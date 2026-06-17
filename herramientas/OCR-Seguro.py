import os
import sys
import base64
import subprocess
import requests
from dotenv import load_dotenv

# Cargar variables de entorno del proyecto
load_dotenv(r"C:\JARVIS2\.env")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    GEMINI_KEY = GEMINI_KEY.strip("'\"")

def comprobar_conexion():
    """Verifica si hay conexión a internet para usar la API de Gemini."""
    try:
        requests.get("https://generativelanguage.googleapis.com", timeout=2)
        return True
    except Exception:
        return False

def ocr_gemini(ruta_archivo):
    """
    Opción 1 (El Mejor): Utiliza la API de Gemini 2.5 Flash para extraer el texto/OCR.
    Soporta tanto imágenes como PDFs directamente.
    """
    if not GEMINI_KEY:
        return None

    # Determinar el tipo de contenido
    ext = os.path.splitext(ruta_archivo)[1].lower()
    mime_type = "image/jpeg"
    if ext in [".png"]: mime_type = "image/png"
    elif ext in [".webp"]: mime_type = "image/webp"
    elif ext in [".pdf"]: mime_type = "application/pdf"

    try:
        with open(ruta_archivo, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": "Analiza este documento o imagen. Extrae y devuelve TODO el texto visible de forma literal y estructurada (OCR)."
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_data
                        }
                    }
                ]
            }]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=45)
        response.raise_for_status()
        
        result = response.json()
        candidates = result.get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[OCR-SEGURO] Error en la llamada a Gemini: {e}", file=sys.stderr)
    return None

def extraer_texto_pdf_impresora(ruta_pdf):
    """
    Opción 2 (El Probable): Lee el texto plano de un PDF escaneado con el OCR de la impresora.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(ruta_pdf)
        texto_paginas = []
        for i, page in enumerate(reader.pages):
            texto = page.extract_text()
            if texto and texto.strip():
                texto_paginas.append(f"--- PÁGINA {i+1} ---\n{texto.strip()}")
        
        if texto_paginas:
            return "\n\n".join(texto_paginas)
    except Exception as e:
        print(f"[OCR-SEGURO] Error al extraer texto plano del PDF: {e}", file=sys.stderr)
    return None

def ocr_local_windows(ruta_imagen):
    """
    Opción 3 (El Seguro): Llama al script de PowerShell para el OCR nativo de Windows 11.
    """
    try:
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", r"C:\JARVIS2\herramientas\OCR-Nativo-Windows.ps1",
            "-ImagePath", ruta_imagen
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[OCR-SEGURO] Error en PowerShell OCR: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"[OCR-SEGURO] Error al invocar PowerShell OCR: {e}", file=sys.stderr)
    return None

def extraer_imagenes_de_pdf(ruta_pdf):
    """
    Extrae las imágenes de un PDF de forma local para poder aplicarles el OCR de Windows.
    """
    rutas_imagenes = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(ruta_pdf)
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        
        for i, page in enumerate(reader.pages):
            for j, image_file in enumerate(page.images):
                nombre_img = f"temp_pdf_page_{i+1}_img_{j+1}.jpg"
                ruta_img = os.path.join(temp_dir, nombre_img)
                with open(ruta_img, "wb") as fp:
                    fp.write(image_file.data)
                rutas_imagenes.append(ruta_img)
    except Exception as e:
        print(f"[OCR-SEGURO] Error al extraer imágenes del PDF: {e}", file=sys.stderr)
    return rutas_imagenes

def procesar_ocr_seguro(ruta_archivo):
    if not os.path.exists(ruta_archivo):
        return f"Error: No existe el archivo '{ruta_archivo}'."

    ext = os.path.splitext(ruta_archivo)[1].lower()
    es_pdf = ext == ".pdf"

    # 1. Opción 1: Gemini en la nube (El mejor - Requiere conexión)
    if comprobar_conexion() and GEMINI_KEY:
        print("[OCR-SEGURO] Intentando Opción 1: Gemini en la Nube...")
        texto = ocr_gemini(ruta_archivo)
        if texto:
            return texto

    # 2. Opción 2: PDF con texto plano de la Impresora (El probable - Local/Offline)
    if es_pdf:
        print("[OCR-SEGURO] Gemini no disponible. Intentando Opción 2: PDF con texto de la Impresora...")
        texto = extraer_texto_pdf_impresora(ruta_archivo)
        if texto:
            return texto

        # Si el PDF no tiene texto y estamos offline, extraemos sus imágenes para aplicar el paso 3
        print("[OCR-SEGURO] El PDF no contiene texto plano. Extrayendo imágenes internas...")
        imagenes_extraidas = extraer_imagenes_de_pdf(ruta_archivo)
        if imagenes_extraidas:
            textos_ocr = []
            for img in imagenes_extraidas:
                txt_ocr = ocr_local_windows(img)
                if txt_ocr:
                    textos_ocr.append(txt_ocr)
                # Limpiar archivo temporal
                try: os.remove(img)
                except Exception: pass
            if textos_ocr:
                return "\n\n--- TEXTO EXTRAÍDO DEL PDF (OCR WINDOWS) ---\n" + "\n\n".join(textos_ocr)

    # 3. Opción 3: Windows OCR Nativo (El seguro - Local/Offline)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
        print("[OCR-SEGURO] Gemini no disponible. Intentando Opción 3: OCR Nativo de Windows 11...")
        texto = ocr_local_windows(ruta_archivo)
        if texto:
            return texto

    return "ERROR: No se pudo extraer texto. Sin conexión a internet y el documento no tiene formato de texto plano ni soporte local."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python OCR-Seguro.py <ruta_del_archivo>")
        sys.exit(1)

    ruta = sys.argv[1].strip('"\'')
    resultado = procesar_ocr_seguro(ruta)
    print(resultado)
