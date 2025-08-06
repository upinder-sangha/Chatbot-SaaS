import os
import uuid
import logging
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from config import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, COLLECTION_NAME

# Set up logging
logger = logging.getLogger(__name__)

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
    
    # Initialize Qdrant client directly
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    # Create collection if it doesn't exist (with proper indexes)
    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        
        # Create indexes for metadata fields we want to filter on
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.bot_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.email",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.name",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        
        logger.info(f"Created new collection {COLLECTION_NAME} with indexes")
    
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
    
    logger.info(f"Stored embedding for bot_id: {bot_id}, email: {email}")
    return bot_id