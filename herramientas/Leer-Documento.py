import sys
import os
try:
    from markitdown import MarkItDown
except ImportError:
    print("Error: La librería 'markitdown' no está instalada. Ejecuta: pip install markitdown")
    sys.exit(1)

def leer_documento(ruta):
    if not os.path.exists(ruta):
        print(f"Error: No se encontró el archivo '{ruta}'.")
        return

    try:
        md = MarkItDown()
        print(f"=== TRADUCIENDO A MARKDOWN: {os.path.basename(ruta)} ===")
        resultado = md.convert(ruta)
        
        # Limitamos la salida a unos 8000 caracteres para no reventar la memoria de contexto de JARVIS
        texto = resultado.text_content
        if len(texto) > 8000:
            texto = texto[:8000] + "\n\n[... AVISO DE JARVIS: El documento era demasiado largo. He cortado la lectura para no saturarme. ...]"
            
        print(texto)
            
    except Exception as e:
        print(f"Error al leer el documento con MarkItDown: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python Leer-Documento.py <ruta_del_documento>")
        sys.exit(1)
        
    ruta_doc = sys.argv[1]
    leer_documento(ruta_doc)
