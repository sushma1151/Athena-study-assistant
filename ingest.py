"""
Document ingestion: extract text from PDFs and split into chunks
ready for embedding (Phase 2).
"""
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file, page by page.
    """
    reader = PdfReader(file_path)
    full_text = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        full_text.append(page_text)

    return "\n".join(full_text)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Splits text into overlapping chunks so retrieval later can find
    relevant sections without losing context at chunk boundaries.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks