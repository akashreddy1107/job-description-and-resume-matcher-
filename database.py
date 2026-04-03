import sqlite3
import os
import uuid
import datetime

# Professional path handling for PythonAnywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "resume_analyzer.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            hr_username TEXT,
            session_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            filename TEXT,
            file_path TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    
    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT, -- 'user' or 'assistant'
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    
    conn.commit()
    conn.close()

def create_session(hr_username, session_name="New Analysis"):
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, hr_username, session_name) VALUES (?, ?, ?)",
        (session_id, hr_username, session_name)
    )
    conn.commit()
    conn.close()
    return session_id

def get_sessions(hr_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, session_name, created_at FROM sessions WHERE hr_username = ? ORDER BY created_at DESC",
        (hr_username,)
    )
    sessions = cursor.fetchall()
    conn.close()
    return [{"id": s[0], "session_name": s[1], "created_at": s[2]} for s in sessions]

def add_document(session_id, filename, file_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (session_id, filename, file_path) VALUES (?, ?, ?)",
        (session_id, filename, file_path)
    )
    conn.commit()
    conn.close()

def get_documents(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename, file_path FROM documents WHERE session_id = ?",
        (session_id,)
    )
    docs = cursor.fetchall()
    conn.close()
    return [{"filename": d[0], "file_path": d[1]} for d in docs]

def add_message(session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_messages(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )
    msgs = cursor.fetchall()
    conn.close()
    return [{"role": m[0], "content": m[1], "timestamp": m[2]} for m in msgs]

# Initialize db right away when imported
init_db()
