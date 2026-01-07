import uuid
import requests
from fastapi import APIRouter
from qdrant_client.models import PointStruct

from models import CreateRequest, CreateChunksRequest, ReadRequest
from embeddings import embed
from chunking import chunk_text
from database import client
from config import COLLECTION, QDRANT_URL, QDRANT_API_KEY


from models import EmbedPreviewRequest

router = APIRouter()

@router.post("/create")
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


@router.post("/create_chunks")
def create_chunks(data: CreateChunksRequest):
    chunks = chunk_text(data.text, data.chunk_size, data.overlap)
    ids = []

    for chunk in chunks:
        vector = embed(chunk)
        point_id = str(uuid.uuid4())

        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": chunk, "type": "chunk"}
                )
            ]
        )
        ids.append(point_id)

    return {"message": "chunked content stored", "chunks_stored": len(ids), "ids": ids}


@router.post("/read")
def read(data: ReadRequest):
    query_vector = embed(data.query)

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

    results = [h["payload"]["text"] for h in hits if "text" in h.get("payload", {})]

    return {"query": data.query, "results": results}


@router.post("/embed_preview")
def embed_preview(data: EmbedPreviewRequest):
    vector = embed(data.text)

    return {
        "text": data.text,
        "vector_length": len(vector),
        "vector_preview": vector[:data.preview_size]
    }
