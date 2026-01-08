
import re

def chunk_text(text: str):
    """
    Sentence-based chunking.
    Each sentence becomes one chunk.
    """
    if not text or not isinstance(text, str):
        return []

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Clean sentences
    chunks = [s.strip() for s in sentences if s.strip()]

    return chunks
