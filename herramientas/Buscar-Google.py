import sys
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el .env en la raíz de JARVIS2
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

def buscar_en_google(query, num_resultados=3):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    
    if not api_key or not cx or api_key == "tu_google_api_key_aqui":
        return "[ERROR] Faltan las claves GOOGLE_API_KEY y GOOGLE_CX en el archivo .env. Debes configurarlas para usar Google."
        
    print(f"\n[JARVIS-RED] Buscando en Google: '{query}'...")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cx,
        'num': num_resultados
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'items' not in data:
            return f"No se encontraron resultados en Google para '{query}'."
            
        res_texto = f"RESULTADOS DE GOOGLE PARA '{query.upper()}':\n"
        for i, item in enumerate(data['items'], 1):
            titulo = item.get('title', 'Sin título')
            link = item.get('link', '')
            snippet = item.get('snippet', 'Sin descripción')
            
            res_texto += f"\n{i}. {titulo}\n"
            res_texto += f"   Resumen: {snippet}\n"
            res_texto += f"   Enlace: {link}\n"
            
        return res_texto
        
    except Exception as e:
        return f"[ERROR CRÍTICO] Fallo de conexión con Google API: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python Buscar-Google.py \"término de búsqueda\" [cantidad]")
        sys.exit(1)
        
    query = sys.argv[1]
    cantidad = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    texto = buscar_en_google(query, cantidad)
    print(texto)
