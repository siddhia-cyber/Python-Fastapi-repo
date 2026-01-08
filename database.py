

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError("QDRANT_URL or QDRANT_API_KEY not set")


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def init_collection():
    try:
        client.get_collection(COLLECTION)
    except:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )


