import sys
import os
import argparse
import chromadb
from chromadb.utils import embedding_functions

# Ruta sagrada de la nueva memoria
DB_PATH = r"C:\JARVIS2\vector_db"

def obtener_coleccion():
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        # Nomic-embed-text: súper rápido y ligero
        ollama_ef = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        return client.get_or_create_collection(
            name="jarvis_memory",
            embedding_function=ollama_ef
        )
    except Exception as e:
        print(f"[ERROR CRÍTICO] No se pudo conectar a la DB Vectorial: {e}")
        sys.exit(1)

def add_document(doc_path):
    if not os.path.exists(doc_path):
        print(f"[ERROR] No se encuentra el archivo: {doc_path}")
        return

    print(f"[JARVIS] Ingestando documento en el hipocampo: {doc_path}")
    doc_id = os.path.basename(doc_path)
    
    try:
        with open(doc_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return

    # Fragmentación básica para no ahogar al modelo (1000 caracteres por trozo)
    chunk_size = 1000
    overlap = 200
    chunks = []
    
    # Fragmentación con solapamiento para no cortar ideas por la mitad
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    
    docs = []
    ids = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        docs.append(chunk)
        ids.append(f"{doc_id}_chunk_{i}")
        metadatas.append({"source": doc_id, "chunk_index": i})
        
    coleccion = obtener_coleccion()
    coleccion.add(
        documents=docs,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"[ÉXITO] Añadidos {len(docs)} fragmentos conceptuales a la memoria infinita.")

def main():
    parser = argparse.ArgumentParser(description="Gestor de Memoria Vectorial de JARVIS")
    parser.add_argument("archivo", type=str, help="Ruta al archivo a memorizar (txt, md, json, etc)")
    args = parser.parse_args()
    add_document(args.archivo)

if __name__ == "__main__":
    main()
