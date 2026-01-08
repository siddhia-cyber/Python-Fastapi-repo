import uuid
import requests
from fastapi import APIRouter
from qdrant_client.models import PointStruct
import pandas as pd

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


# @router.post("/read")
# def read(data: ReadRequest):
#     query_vector = embed(data.query)

#     response = requests.post(
#         f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
#         headers={
#             "api-key": QDRANT_API_KEY,
#             "Content-Type": "application/json"
#         },
#         json={
#             "vector": query_vector,
#             "limit": data.top_k,
#             "with_payload": True
#         },
#         timeout=30
#     )

#     if response.status_code != 200:
#         return {
#             "error": "Qdrant search failed",
#             "details": response.text
#         }

#     hits = response.json().get("result", [])

#     MIN_SCORE = 0.65 
    

#     results = []
#     for h in hits:
#         score = h.get("score", 0)
#         payload = h.get("payload", {})

#         if score >= MIN_SCORE:
#             results.append({
#                 "text": payload.get("text", ""),
#                 "source": payload.get("source", "unknown"),
#                 "score": score
#             })

#     return {
#         "query": data.query,
#         "results": results
#     }


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

    hits = response.json().get("result", [])

    results = []
    for h in hits:
        payload = h.get("payload", {})
        results.append({
            "text": payload.get("text", ""),
            "source": payload.get("source", "unknown"),
            "similarity_score": round(h.get("score", 0), 4)
        })

    return {
        "query": data.query,
        "results": results
    }

      















@router.post("/embed_preview")
def embed_preview(data: EmbedPreviewRequest):
    vector = embed(data.text)

    return {
        "text": data.text,
        "vector_length": len(vector),
        "vector_preview": vector[:data.preview_size]
    }



from pathlib import Path

@router.post("/index_corpus")
def index_corpus():
    corpus_dir = Path("corpus")

    if not corpus_dir.exists():
        return {"error": "corpus folder not found"}

    total_chunks = 0

    for file in corpus_dir.glob("*.txt"):
        text = file.read_text(encoding="utf-8")

       
        #chunks = chunk_text(text, chunk_size=300, overlap=50) 
        chunks = chunk_text(text)
        

        print("DEBUG → Number of chunks:", len(chunks))
        print("DEBUG → Chunks:", chunks)

 

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
                            "source": file.name
                        }
                    )
                ]
            )
            total_chunks += 1

    return {
        "message": "Corpus indexed successfully",
        "chunks_indexed": total_chunks
    }





@router.get("/export_vectors")
def export_vectors():
    try:
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
            headers={
                "api-key": QDRANT_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "limit": 100,
                "with_vector": True,
                "with_payload": True
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        points = data.get("result", {}).get("points", [])

        if not points:
            return {"error": "No vectors found in database"}

        rows = []
        for p in points:
            payload = p.get("payload") or {}
            vector = p.get("vector") or []

            rows.append({
                "text": payload.get("text", ""),
                "source": payload.get("source", ""),
                "vector_length": len(vector),
                "embedding": str(vector)  # stringify to avoid Excel crash
            })

        df = pd.DataFrame(rows)

        file_path = "vector_database.xlsx"
        df.to_excel(file_path, index=False)

        return {
            "message": "Vector database exported successfully",
            "rows": len(df),
            "file": file_path
        }

    except Exception as e:
        return {
            "error": "Export failed",
            "details": str(e)
        }
