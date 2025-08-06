import os
import logging
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType, Distance, VectorParams

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
COLLECTION_NAME = "docative"  # Use your actual collection name
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def fix_collection_indexes():
    """One-time script to create collection with required indexes"""
    logger.info("Starting collection setup...")
    
    # Initialize Qdrant client
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if COLLECTION_NAME not in collection_names:
        logger.info(f"Collection {COLLECTION_NAME} does not exist. Creating it...")
        
        # Create the collection with proper vector configuration
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        
        logger.info(f"✅ Created collection {COLLECTION_NAME}")
    else:
        logger.info(f"Collection {COLLECTION_NAME} already exists.")
    
    # Now ensure all required indexes exist
    indexes_to_create = [
        ("metadata.bot_id", "bot_id"),
        ("metadata.email", "email"),
        ("metadata.name", "name")
    ]
    
    for field_path, field_name in indexes_to_create:
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_path,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info(f"✅ Created index for {field_name}")
        except Exception as e:
            logger.info(f"⚠️ Index for {field_name} already exists or error: {str(e)}")
    
    logger.info("Collection setup completed!")

if __name__ == "__main__":
    fix_collection_indexes()