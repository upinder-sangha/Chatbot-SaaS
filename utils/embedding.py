import os
import uuid
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, COLLECTION_NAME

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

async def store_embedding(text: str, email: str, name: str) -> str:
    # Generate a unique bot_id
    bot_id = str(uuid.uuid4())

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len
    )

    # Split text into chunks
    chunks = text_splitter.split_text(text)

    # Initialize LangChain embeddings
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)

    # Create Qdrant vector store
    vectorstore = QdrantVectorStore.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=[{"bot_id": bot_id, "email": email, "name": name} for _ in chunks],
        ids=[str(uuid.uuid4()) for _ in chunks],
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
    )

    return bot_id