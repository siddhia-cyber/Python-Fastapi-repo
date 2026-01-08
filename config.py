import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

EMBED_URL = os.getenv("EMBED_URL")
EMBED_MODEL = os.getenv("EMBED_MODEL")

COLLECTION = "Corpus"

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError("QDRANT config missing")

if not EMBED_URL or not EMBED_MODEL:
    raise RuntimeError("Embedding config missing")


