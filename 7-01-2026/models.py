from pydantic import BaseModel

class CreateRequest(BaseModel):
    text: str

class CreateChunksRequest(BaseModel):
    text: str
    chunk_size: int = 300
    overlap: int = 50

class ReadRequest(BaseModel):
    query: str
    top_k: int = 3

class EmbedPreviewRequest(BaseModel):
    text: str
    preview_size: int = 10
