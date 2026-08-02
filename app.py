"""
Athena - RAG + Agent Assistant
Main Flask application entry point.
"""
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import functools

from config import Config
from ingest import extract_text_from_pdf, chunk_text
from embed import embed_chunks
from chroma_store import add_chunks, delete_document_chunks
from retrive import retrieve_relevant_chunks
from llm import generate_answer
from models import (
    save_document, save_chat, get_chat_history, get_all_documents, delete_document,
    create_user, get_user_by_username, verify_user
)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "..", "frontend")


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/<path:filename>")
def serve_frontend_file(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


@app.route("/api/status")
def status():
    return jsonify({"status": "ok", "message": "Athena backend is running"})


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "That username is already taken"}), 400

    user_id = create_user(username, password)
    session["user_id"] = user_id
    session["username"] = username
    return jsonify({"message": "Account created", "username": username})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = verify_user(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"message": "Logged in", "username": user["username"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": session.get("username")})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported right now"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        text = extract_text_from_pdf(save_path)
    except Exception as e:
        return jsonify({"error": f"Failed to extract text: {str(e)}"}), 500

    chunks = chunk_text(text)

    embeddings = embed_chunks(chunks)
    add_chunks(document_id=file.filename, chunks=chunks, embeddings=embeddings)

    try:
        save_document(
            user_id=session["user_id"],
            filename=file.filename,
            num_chunks=len(chunks),
            num_characters=len(text)
        )
    except Exception as e:
        print(f"Warning: could not save document to MySQL: {e}")

    return jsonify({
        "filename": file.filename,
        "num_characters": len(text),
        "num_chunks": len(chunks),
        "preview_chunk": chunks[0] if chunks else None
    })


@app.route("/api/query", methods=["POST"])
@login_required
def query_document():
    data = request.get_json(force=True)
    filename = data.get("filename")
    question = data.get("question")
    mode = data.get("mode", "ask")

    if not filename or not question:
        return jsonify({"error": "filename and question are required"}), 400

    relevant_chunks = retrieve_relevant_chunks(document_id=filename, question=question, top_k=4)

    if not relevant_chunks:
        return jsonify({"answer": "No relevant content found for that question yet."})

    answer = generate_answer(mode=mode, question=question, context_chunks=relevant_chunks)

    try:
        save_chat(
            user_id=session["user_id"],
            filename=filename,
            mode=mode,
            question=question,
            answer=answer
        )
    except Exception as e:
        print(f"Warning: could not save chat to MySQL: {e}")

    return jsonify({"answer": answer})


@app.route("/api/history", methods=["GET"])
@login_required
def chat_history():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "filename query parameter is required"}), 400

    try:
        history = get_chat_history(user_id=session["user_id"], filename=filename)
    except Exception as e:
        return jsonify({"error": f"Could not fetch history: {str(e)}"}), 500

    return jsonify({"history": history})


@app.route("/api/documents", methods=["GET"])
@login_required
def list_documents():
    try:
        documents = get_all_documents(user_id=session["user_id"])
    except Exception as e:
        return jsonify({"error": f"Could not fetch documents: {str(e)}"}), 500

    return jsonify({"documents": documents})

@app.route("/api/documents/<path:filename>", methods=["DELETE"])
@login_required
def delete_document_route(filename):
    try:
        delete_document(user_id=session["user_id"], filename=filename)
        delete_document_chunks(document_id=filename)
    except Exception as e:
        return jsonify({"error": f"Could not delete document: {str(e)}"}), 500

    return jsonify({"message": f"Deleted {filename}"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)