import chromadb

# Crear cliente de Chroma
chroma_client = chromadb.Client()

# Obtener todas las colecciones existentes
collections = chroma_client.list_collections()

# Eliminar todas las colecciones
for collection in collections:
    chroma_client.delete_collection(collection.name)

print("Todas las colecciones han sido eliminadas.")
