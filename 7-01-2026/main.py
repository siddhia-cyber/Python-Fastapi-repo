
import os
from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI
from pydantic import BaseModel
import requests
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError("QDRANT_URL or QDRANT_API_KEY not set in .env")

COLLECTION = "docs"

EMBED_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"

app = FastAPI()

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

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



def embed(text: str):
    r = requests.post(
        EMBED_URL,
        json={"model": MODEL, "prompt": text},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["embedding"]

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    """
    Splits text into overlapping word chunks.
    - chunk_size: number of words per chunk
    - overlap: words shared between consecutive chunks
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  

    return chunks
class CreateRequest(BaseModel):
    text: str
class CreateChunksRequest(BaseModel):
    text: str
    chunk_size: int = 300
    overlap: int = 50


class ReadRequest(BaseModel):
    query: str
    top_k: int = 3


@app.post("/create")
def create(data: CreateRequest):
    vector = embed(data.text)
    point_id = str(uuid.uuid4())

    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"text": data.text}
            )
        ]
    )

    return {"message": "stored", "id": point_id}


@app.post("/create_chunks")
def create_chunks(data: CreateChunksRequest):
    chunks = chunk_text(
        data.text,
        chunk_size=data.chunk_size,
        overlap=data.overlap
    )

    stored_ids = []

    for chunk in chunks:
        vector = embed(chunk)
        point_id = str(uuid.uuid4())

        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "type": "chunk"
                    }
                )
            ]
        )

        stored_ids.append(point_id)

    return {
        "message": "chunked content stored",
        "chunks_stored": len(stored_ids),
        "ids": stored_ids
    }

@app.post("/read")
def read(data: ReadRequest):
    # Embed query
    query_vector = embed(data.query)

    # Call Qdrant REST API directly
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        headers={
            "api-key": QDRANT_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "vector": query_vector,
            "limit": data.top_k,
            "with_payload": True
        },
        timeout=30
    )

    response.raise_for_status()
    hits = response.json().get("result", [])

    results = []
    for h in hits:
        payload = h.get("payload", {})
        if "text" in payload:
            results.append(payload["text"])

    return {
        "query": data.query,
        "results": results
    }
