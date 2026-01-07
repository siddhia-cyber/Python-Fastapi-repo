from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def init_collection():
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )
