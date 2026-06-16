import sys
import requests
import xml.etree.ElementTree as ET

def buscar_noticias_rss(max_resultados=5):
    print("\n[JARVIS-RED] Conectando a fuentes de noticias seguras (RSS)...")
    url = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada" # Portada general
    
    try:
        # Añadir cabecera para simular navegador y evitar bloqueos básicos
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        respuesta = requests.get(url, headers=headers, timeout=10)
        respuesta.raise_for_status()
        
        # Parsear el XML del RSS
        root = ET.fromstring(respuesta.content)
        
        res_texto = "ÚLTIMAS NOTICIAS (TITULARES PRINCIPALES):\n"
        contador = 0
        
        for item in root.findall('./channel/item'):
            if contador >= max_resultados:
                break
                
            titulo = item.find('title').text if item.find('title') is not None else 'Sin título'
            link = item.find('link').text if item.find('link') is not None else ''
            
            # Limpiar etiquetas HTML básicas del resumen
            descripcion = item.find('description').text if item.find('description') is not None else ''
            import re
            descripcion_limpia = re.sub('<[^<]+>', '', descripcion).strip()
            
            res_texto += f"\n{contador + 1}. {titulo}\n"
            if descripcion_limpia:
                res_texto += f"   Resumen: {descripcion_limpia}\n"
            res_texto += f"   Enlace: {link}\n"
            
            contador += 1
            
        return res_texto
            
    except Exception as e:
        return f"[ERROR CRÍTICO] Fallo de conexión de red: {e}"

if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    texto = buscar_noticias_rss(cantidad)
    print(texto)
