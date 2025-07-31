# config.py

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# LLM model
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 1
LLM_MAX_TOKENS = 1000

# Retrieval
TOP_K_CHUNKS = 5

# Qdrant
COLLECTION_NAME = "bots"
