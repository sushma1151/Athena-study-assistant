# Athena — RAG + Agent Study Assistant

Athena is a full-stack study assistant that lets you upload a PDF and then **ask questions, generate summaries, or create quizzes** from its content — powered by a RAG (Retrieval-Augmented Generation) pipeline and a real LLM.

Built as a personal project while preparing for SSC CHSL, combining a Flask backend, vector search, MySQL persistence, and a custom-designed frontend.

## Features

- **User accounts** — secure signup/login with hashed passwords, per-user data isolation
- **PDF upload & processing** — text extraction and chunking for any uploaded document
- **Semantic search (RAG)** — embeddings via `sentence-transformers`, stored and queried through ChromaDB
- **AI-generated answers** — powered by Google's Gemini API, with three modes:
  - **Ask a Doubt** — get a direct answer sourced from the document
  - **Summarize** — get a concise summary of the material
  - **Generate Quiz** — auto-generate quiz questions and answers
- **Multi-document sidebar** — switch between uploaded documents, each with its own saved chat history
- **Delete & New Chat** — manage documents and start fresh conversations anytime
- **Persistent history** — every document and chat exchange is saved in MySQL, restored automatically on login

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Database | MySQL |
| Vector store | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Google Gemini API |
| Frontend | HTML, CSS, vanilla JavaScript |
| Auth | Flask sessions + Werkzeug password hashing |

## Project Structure

```
athena/
├── backend/
│   ├── app.py            # Flask routes (auth, upload, query, history, documents)
│   ├── config.py         # Environment-based configuration
│   ├── ingest.py         # PDF text extraction + chunking
│   ├── embed.py          # Text-to-vector embeddings
│   ├── chroma_store.py   # ChromaDB storage and retrieval
│   ├── retrive.py         # Semantic search logic
│   ├── llm.py             # Gemini API integration + prompt building
│   ├── models.py          # MySQL operations (users, documents, chat history)
│   └── schema.sql         # Database schema
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── uploads/                # Uploaded PDFs (not committed)
└── requirements.txt
```

## Setup

### 1. Clone and install dependencies
```bash
cd backend
pip install -r ../requirements.txt --break-system-packages
```

### 2. Set up MySQL
Run the schema in `backend/schema.sql` to create the database and tables:
```bash
mysql -u root -p < schema.sql
```

### 3. Configure environment variables
Create a `.env` file inside `backend/`:
```
GEMINI_API_KEY=your_gemini_api_key_here
MYSQL_PASSWORD=your_mysql_password_here
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 4. Run the server
```bash
python app.py
```

Visit `http://127.0.0.1:5000` — the frontend is served directly by Flask.

## How It Works

1. **Upload** — a PDF is uploaded, text is extracted, and split into overlapping chunks
2. **Embed** — each chunk is converted into a vector using a local embedding model (no API cost)
3. **Store** — vectors are saved in ChromaDB, tagged by document
4. **Retrieve** — when you ask a question, your query is embedded and compared against stored chunks to find the most relevant ones
5. **Generate** — the relevant chunks are sent to Gemini along with your question (or a summarize/quiz instruction), and the model generates a grounded response
6. **Persist** — the full exchange is saved to MySQL, tied to your account and the document

## Notes

- `.env`, `uploads/`, and `chroma_store/` are excluded from version control — see `.gitignore`
- This is a personal/educational project and uses Flask's development server; not configured for production deployment
