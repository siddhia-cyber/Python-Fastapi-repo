# from fastapi import FastAPI
# from pydantic import BaseModel
# from qdrant_client import QdrantClient
# from qdrant_client.models import VectorParams, Distance, PointStruct
# import requests
# import uuid

# # -----------------------------
# # APP
# # -----------------------------
# app = FastAPI()

# # -----------------------------
# # QDRANT (CLOUD – NO DOCKER)
# # -----------------------------
# client = QdrantClient(
#     url="https://39d0a3df-03af-4e63-be36-0b76528fc074.europe-west3-0.gcp.cloud.qdrant.io",
#     api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.P5Ip3rwWbEQPsE6xMbiu3D7OYcBb03dTqvjS7O9avOs"
# )

# COLLECTION = "docs"

# try:
#     client.get_collection(COLLECTION)
# except Exception:
#     client.create_collection(
#         collection_name=COLLECTION,
#         vectors_config=VectorParams(
#             size=768,
#             distance=Distance.COSINE
#         )
#     )


# # -----------------------------
# # OLLAMA EMBEDDINGS
# # -----------------------------
# EMBED_URL = "http://localhost:11434/api/embeddings"
# MODEL = "nomic-embed-text"

# def embed(text: str):
#     try:
#         r = requests.post(
#             EMBED_URL,
#             json={"model": MODEL, "prompt": text},
#             timeout=30
#         )
#         r.raise_for_status()
#         data = r.json()
#         if "embedding" not in data:
#             raise ValueError("No embedding in response")
#         return data["embedding"]
#     except Exception as e:
#         raise RuntimeError(f"Embedding failed: {e}")


# # -----------------------------
# # REQUEST MODELS
# # -----------------------------
# class CreateRequest(BaseModel):
#     text: str

# class ReadRequest(BaseModel):
#     query: str
#     top_k: int = 3

# # -----------------------------
# # CREATE
# # -----------------------------
# @app.post("/create")
# def create(data: CreateRequest):
#     vec = embed(data.text)
#     pid = str(uuid.uuid4())

#     client.upsert(
#         collection_name=COLLECTION,
#         points=[
#             PointStruct(
#                 id=pid,
#                 vector=vec,
#                 payload={"text": data.text}
#             )
#         ]
#     )

#     return {"message": "stored", "id": pid}

# # -----------------------------
# # READ
# @app.post("/read")
# def read(data: ReadRequest):
#     # 1️⃣ Embed query
#     try:
#         qvec = embed(data.query)
#     except Exception as e:
#         return {"error": "Embedding failed", "details": str(e)}

#     # 2️⃣ Call Qdrant REST API directly
#     try:
#         response = requests.post(
#             f"{client.url}/collections/{COLLECTION}/points/search",
#             headers={
#                 "api-key": client.api_key,
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "vector": qvec,
#                 "limit": data.top_k,
#                 "with_payload": True
#             },
#             timeout=30
#         )

#         response.raise_for_status()
#         hits = response.json()["result"]

#     except Exception as e:
#         return {"error": "Search failed", "details": str(e)}

#     # 3️⃣ Extract results
#     results = []
#     for h in hits:
#         payload = h.get("payload", {})
#         if "text" in payload:
#             results.append(payload["text"])

#     return {
#         "query": data.query,
#         "results": results
#     }





from fastapi import FastAPI
from pydantic import BaseModel
import requests
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct


# =====================================================
# CONFIG (PASTE YOUR DETAILS HERE)
# =====================================================

QDRANT_URL = "https://39d0a3df-03af-4e63-be36-0b76528fc074.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.P5Ip3rwWbEQPsE6xMbiu3D7OYcBb03dTqvjS7O9avOs"

COLLECTION = "docs"

EMBED_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI()


# =====================================================
# QDRANT CLIENT (USED ONLY FOR CREATE)
# =====================================================

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Create collection ONLY if it does not exist
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


# =====================================================
# EMBEDDING FUNCTION (OLLAMA)
# =====================================================

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
        start = end - overlap  # overlap for better context continuity

    return chunks










# =====================================================
# REQUEST MODELS
# =====================================================

class CreateRequest(BaseModel):
    text: str
class CreateChunksRequest(BaseModel):
    text: str
    chunk_size: int = 300
    overlap: int = 50


class ReadRequest(BaseModel):
    query: str
    top_k: int = 3


# =====================================================
# CREATE API (STORE VECTORS)
# =====================================================

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










# =====================================================
# READ API (VECTOR SEARCH — PURE REST, NO SDK)
# =====================================================

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
