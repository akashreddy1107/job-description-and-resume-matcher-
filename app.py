from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import subprocess
import sys
from dotenv import load_dotenv
import rag_query

# Load environment variables using absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

HF_TOKEN = os.getenv("HF_TOKEN", "")
HR_USERNAME = os.getenv("HR_USERNAME", "hr_admin")
HR_PASSWORD = os.getenv("HR_PASSWORD", "Resume@2024")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

app = Flask(__name__)
app.secret_key = SECRET_KEY

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def login_required(f):
    """Decorator to protect routes — redirects to login if not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("hr_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("hr_logged_in"):
        return redirect(url_for("home"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == HR_USERNAME and password == HR_PASSWORD:
            session["hr_logged_in"] = True
            session["hr_username"] = username
            return redirect(url_for("home"))
        else:
            error = "Invalid credentials. Please check your username and password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


import database
import ingest

# ── Main App Routes ───────────────────────────────────────────────────────────

@app.route("/")
@login_required
def home():
    hr_user = session.get("hr_username", "HR")
    sessions_list = database.get_sessions(hr_user)
    return render_template("index.html", hr_user=hr_user, sessions=sessions_list)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    files = request.files.getlist("resume")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"success": False, "message": "No files provided"}), 400

    hr_user = session.get("hr_username")
    session_name = files[0].filename if len(files) == 1 else f"Batch: {len(files)} Resumes"
    session_id = database.create_session(hr_user, session_name=session_name)

    files_info = []
    for f in files:
        if f.filename == "": continue
        name, ext = os.path.splitext(f.filename)
        if ext.lower() not in ['.pdf', '.doc', '.docx']:
            continue
            
        safe_filename = f"{session_id}_{f.filename}"
        path = os.path.join(UPLOAD_FOLDER, safe_filename)
        f.save(path)
        
        database.add_document(session_id, f.filename, path)
        files_info.append({"filename": f.filename, "file_path": path})

    if not files_info:
        return jsonify({"success": False, "message": "Only PDF and Word documents are supported"}), 400

    try:
        num_chunks = ingest.process_files(session_id, files_info, HF_TOKEN)
    except Exception as e:
        return jsonify({"success": False, "message": f"Indexing failed: {str(e)}"}), 500

    return jsonify({
        "success": True, 
        "message": f"Successfully indexed {len(files_info)} document(s)!", 
        "session_id": session_id,
        "session_name": session_name
    })


@app.route("/ask", methods=["POST"])
@login_required
def ask():
    question = request.form.get("question", "").strip()
    session_id = request.form.get("session_id", "").strip()
    
    if not question or not session_id:
        return jsonify({"success": False, "message": "Question or Active Session ID missing"}), 400

    if not HF_TOKEN:
        return jsonify({
            "success": False,
            "message": "HF_TOKEN is not set. Please add your token."
        }), 500

    try:
        answer = rag_query.query(session_id, question, HF_TOKEN)
        
        database.add_message(session_id, "user", question)
        database.add_message(session_id, "assistant", answer)
        
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({"success": False, "message": f"Query failed: {str(e)}"}), 500

@app.route("/evaluate_jd", methods=["POST"])
@login_required
def evaluate_jd():
    jd_text = request.form.get("jd_text", "").strip()
    session_id = request.form.get("session_id", "").strip()
    
    if not jd_text or not session_id:
        return jsonify({"success": False, "message": "Job Description or Active Session ID missing"}), 400

    if not HF_TOKEN:
        return jsonify({"success": False, "message": "HF_TOKEN is not set."}), 500

    try:
        answer = rag_query.evaluate_fit(session_id, jd_text, HF_TOKEN)
        database.add_message(session_id, "user", f"**Requested JD Evaluation for:**\n{jd_text[:100]}...")
        database.add_message(session_id, "assistant", answer)
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({"success": False, "message": f"Evaluation failed: {str(e)}"}), 500

@app.route("/api/session/<session_id>", methods=["GET"])
@login_required
def get_session_data(session_id):
    docs = database.get_documents(session_id)
    msgs = database.get_messages(session_id)
    return jsonify({"success": True, "documents": docs, "messages": msgs})


if __name__ == "__main__":
    if not HF_TOKEN:
        print("⚠️  WARNING: HF_TOKEN is not set. Copy .env.example to .env and add your token.")
    print(f"[HR LOGIN] Username: {HR_USERNAME}  |  Password: {HR_PASSWORD}")

    # Production-ready port handling for cloud hosts (Render/Heroku/etc)
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.getenv("FLASK_PORT", "5000")))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

    if host == "0.0.0.0":
        print("🌐 Listening on all network interfaces — other PCs can use http://<this-computer-LAN-ip>:%d" % port)
        print("   (On Windows, find the IPv4 address in: ipconfig)")

    app.run(host=host, port=port, debug=debug)