import sys
import os
try:
    from pypdf import PdfReader
except ImportError:
    print("Error: La librería 'pypdf' no está instalada. Ejecuta: pip install pypdf")
    sys.exit(1)

def leer_pdf(ruta, num_paginas=None):
    if not os.path.exists(ruta):
        print(f"Error: No se encontró el archivo '{ruta}'.")
        return

    try:
        reader = PdfReader(ruta)
        total_pages = len(reader.pages)
        limite = total_pages if num_paginas is None else min(int(num_paginas), total_pages)
        
        print(f"=== LEYENDO PDF: {os.path.basename(ruta)} ({limite}/{total_pages} páginas) ===")
        texto_completo = []
        for i in range(limite):
            pagina = reader.pages[i]
            texto_completo.append(f"--- PÁGINA {i+1} ---")
            texto_completo.append(pagina.extract_text() or "[Sin texto extraíble en esta página]")
            
        print("\n".join(texto_completo))
        
        if limite < total_pages:
            print(f"\n[Aviso: Solo se mostraron las primeras {limite} páginas de {total_pages}. Para ver más, especifica un límite mayor.]")
            
    except Exception as e:
        print(f"Error al leer el PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python Leer-PDF.py <ruta_del_pdf> [numero_de_paginas]")
        sys.exit(1)
        
    ruta_pdf = sys.argv[1]
    paginas = sys.argv[2] if len(sys.argv) > 2 else 5  # Por defecto lee 5 páginas para no saturar memoria
    leer_pdf(ruta_pdf, paginas)
