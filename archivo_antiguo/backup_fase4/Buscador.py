from ddgs import DDGS

def buscar_en_internet(consulta, max_resultados=3):
    """
    Busca información en internet usando DuckDuckGo, bloqueando explícitamente Wikipedia.
    """
    try:
        # Pedimos más resultados de los necesarios por si tenemos que descartar Wikipedia
        resultados_brutos = DDGS().text(consulta, region='es-es', safesearch='off', max_results=max_resultados + 5)
        
        if hasattr(resultados_brutos, '__iter__') and not isinstance(resultados_brutos, list):
            resultados_brutos = list(resultados_brutos)
            
        if not resultados_brutos:
            return f"No he encontrado información en internet sobre '{consulta}'."
        
        respuesta = f"Resultados para '{consulta}':\n\n"
        resultados_validos = 0
        
        for res in resultados_brutos:
            url = res.get('href', '#')
            
            # REGLA ESTRICTA: Bloquear Wikipedia a fuego
            if 'wikipedia.org' in url.lower():
                continue
                
            titulo = res.get('title', 'Sin título')
            cuerpo = res.get('body', 'Sin contenido')
            
            respuesta += f"--- {titulo} ---\n{cuerpo}\nEnlace: {url}\n\n"
            resultados_validos += 1
            
            # Paramos cuando lleguemos al máximo deseado de resultados limpios
            if resultados_validos >= max_resultados:
                break
                
        if resultados_validos == 0:
            return f"Todos los resultados para '{consulta}' provenían de Wikipedia y han sido descartados."
            
        return respuesta.strip()
    except Exception as e:
        return f"Ha ocurrido un error al buscar en internet: {str(e)}"

import sys
if __name__ == "__main__":
    if len(sys.argv) > 1:
        consulta = " ".join(sys.argv[1:])
        print(buscar_en_internet(consulta, max_resultados=3))
    else:
        print("Error: Proporciona un término de búsqueda. Ejemplo: python Buscador.py \"término\"")
