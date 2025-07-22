import os
import uuid
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

COLLECTION_NAME = "bots"

async def store_embedding(text: str, email: str) -> str:
    # Generate a unique bot_id
    bot_id = str(uuid.uuid4())

    # Split into chunks if too long (simple for now)
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

    vectors = []
    for chunk in chunks:
        response = openai_client.embeddings.create(
            input=chunk,
            model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding

        vectors.append(
            qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "bot_id": bot_id,
                    "email": email,
                    "text": chunk
                }
            )
        )

    # Upsert into Qdrant
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=vectors
    )

    return bot_id
