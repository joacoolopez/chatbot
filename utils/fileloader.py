import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.document_loaders import TextLoader

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la API key de OpenAI desde las variables de entorno
api_key = os.getenv("OPENAI_API_KEY")

# Cargar los documentos desde un archivo
loader = TextLoader("files/Belladerma prueba.txt")  # Ajusta el path de tu archivo
docs = loader.load()

# Imprimir el contenido de la primera página del archivo cargado
print(docs[0].page_content)

# Dividir los documentos en fragmentos más pequeños
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# Crear un vectorstore a partir de los documentos fragmentados
embedding = OpenAIEmbeddings()

# Crear una colección en ChromaDB para almacenar los vectores
vectorstore = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory="path_to_chroma_db")

# Ahora los vectores están almacenados en el directorio especificado

# Si necesitas cargar los vectores más tarde desde el directorio persistido
# puedes hacer esto usando 'from_existing':
vectorstore = Chroma.from_existing(persist_directory="path_to_chroma_db")
