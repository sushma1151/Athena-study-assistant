"""
Wraps ChromaDB: stores chunk embeddings per document, and lets us
search for the most relevant chunks given a query.
"""
import chromadb
from config import Config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
    return _client


def get_collection(name: str = "athena_docs"):
    client = get_client()
    return client.get_or_create_collection(name=name)


def add_chunks(document_id: str, chunks: list[str], embeddings: list[list[float]]):
    if not chunks:
        return

    collection = get_collection()
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )


def query_chunks(document_id: str, query_embedding: list[float], top_k: int = 4):
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": document_id}
    )
    return results

def delete_document_chunks(document_id: str):
    """
    Removes all stored chunks for a given document, so its content
    is no longer searchable once the document is deleted.
    """
    collection = get_collection()
    collection.delete(where={"document_id": document_id})