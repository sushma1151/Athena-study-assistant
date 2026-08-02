"""
Handles all MySQL database operations: user accounts, document
metadata, and chat history - all scoped per user.
"""
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )


def create_user(username: str, password: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, password_hash)
    )
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id


def get_user_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def verify_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None


def save_document(user_id: int, filename: str, num_chunks: int, num_characters: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (user_id, filename, num_chunks, num_characters) VALUES (%s, %s, %s, %s)",
        (user_id, filename, num_chunks, num_characters)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_all_documents(user_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM documents WHERE user_id = %s ORDER BY uploaded_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def save_chat(user_id: int, filename: str, mode: str, question: str, answer: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, filename, mode, question, answer) VALUES (%s, %s, %s, %s, %s)",
        (user_id, filename, mode, question, answer)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_chat_history(user_id: int, filename: str, limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT mode, question, answer, created_at
        FROM chat_history
        WHERE user_id = %s AND filename = %s
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (user_id, filename, limit)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def delete_document(user_id: int, filename: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM chat_history WHERE user_id = %s AND filename = %s",
        (user_id, filename)
    )
    cursor.execute(
        "DELETE FROM documents WHERE user_id = %s AND filename = %s",
        (user_id, filename)
    )
    conn.commit()
    cursor.close()
    conn.close()