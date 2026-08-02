"""
Given a question and a document, finds the most relevant chunks
using embedding similarity search. This is the "R" in RAG.
"""
from embed import embed_query
from chroma_store import query_chunks


def retrieve_relevant_chunks(document_id: str, question: str, top_k: int = 4) -> list[str]:
    query_embedding = embed_query(question)
    results = query_chunks(document_id, query_embedding, top_k=top_k)

    documents = results.get("documents", [[]])
    if not documents or not documents[0]:
        return []

    return documents[0]