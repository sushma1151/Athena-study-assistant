"""
Turns text chunks into embeddings (vectors) using a free, local model.
No API key needed - this runs entirely on your machine.
"""
from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(chunks, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    model = get_model()
    embedding = model.encode([query], show_progress_bar=False)
    return embedding[0].tolist()