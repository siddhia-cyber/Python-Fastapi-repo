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
    all_points = []
    offset = None

    # Scroll through all points in the collection
    while True:
        result = client.scroll(
            collection_name=COLLECTION,
            limit=100,
            offset=offset,
            with_vectors=True,
            with_payload=True
        )

        points, offset = result

        if not points:
            break

        for p in points:
            payload = p.payload or {}
            all_points.append({
                "id": p.id,
                "text": payload.get("text", ""),
                "source": payload.get("source", "unknown"),
                "vector": p.vector
            })

        if offset is None:
            break

    if not all_points:
        return {"message": "No vectors found in database"}

    # Convert to DataFrame
    df = pd.DataFrame(all_points)

    # Save Excel file
    output_path = Path("vector_database.xlsx")
    df.to_excel(output_path, index=False)

    return {
        "message": "Vector database exported successfully",
        "file": str(output_path),
        "total_vectors": len(df)
    }


