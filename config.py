"""
Configuration for Athena backend.
Fill in real values via environment variables in production.
"""
from dotenv import load_dotenv
load_dotenv()
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # MySQL connection (used starting Phase 3 for chat history / documents metadata)
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "athena")

    # LLM API key (Anthropic) - set this as an environment variable, never hardcode
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    # Vector DB storage location (Chroma persists to disk here)
    CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_store")

    # Chunking settings
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100