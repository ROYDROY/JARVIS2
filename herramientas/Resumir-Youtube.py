import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Uso: python Resumir-Youtube.py <URL_DEL_VIDEO>")
        sys.exit(1)
        
    url = sys.argv[1]
    
    # Intentar importar la librería del DLC
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("ERROR: La librería youtube-transcript-api no está instalada.")
        print("Por favor, entra en la interfaz gráfica de JARVIS y activa el módulo 'Devorador de YouTube'.")
        sys.exit(1)
        
    # Extraer ID del video
    video_id = None
    # match for v=XXXX or youtu.be/XXXX
    match1 = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    match2 = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if match1:
        video_id = match1.group(1)
    elif match2:
        video_id = match2.group(1)
    else:
        print("ERROR: No se pudo encontrar un ID válido de YouTube en la URL proporcionada.")
        sys.exit(1)
        
    try:
        # Extraer subtitulos en español o inglés por defecto
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        texto_completo = " ".join([t['text'] for t in transcript])
        
        # Ojo: si el video es muy largo, cortarlo para que no explote el contexto de la IA
        # ~6000 palabras es el límite seguro para qwen2.5:7b con 8k tokens
        palabras = texto_completo.split()
        if len(palabras) > 5000:
            texto_completo = " ".join(palabras[:5000])
            print("AVISO: El vídeo es extremadamente largo. Se ha truncado a las primeras 5000 palabras para evitar saturar el cerebro de la IA.\n")
            
        print("--- SUBTÍTULOS EXTRAÍDOS CON ÉXITO ---")
        print(texto_completo)
        
    except Exception as e:
        print(f"ERROR: No se pudieron obtener los subtítulos. Detalles: {e}")
        print("Es posible que el vídeo no tenga subtítulos automáticos o esté bloqueado.")
        sys.exit(1)

if __name__ == "__main__":
    main()
