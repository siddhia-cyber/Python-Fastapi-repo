import requests
from config import EMBED_URL, EMBED_MODEL

def embed(text: str) -> list:
    response = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30
    )
    response.raise_for_status()
    return response.json()["embedding"]
