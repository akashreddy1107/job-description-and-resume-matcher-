import os
import pickle
import numpy as np
# from sentence_transformers import SentenceTransformer  <-- REMOVED to save 500MB disk space
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Hugging Face Inference API config (all from .env) ────────────────────────
HF_API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# ── Remote Embeddings API ─────────────────────────────────────────────────────
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_API_URL = f"https://router.huggingface.co/hf-inference/models/{EMBED_MODEL_ID}/pipeline/feature-extraction"

def get_embeddings_from_api(texts: list[str], hf_token: str) -> np.ndarray:
    """Gets embeddings from Hugging Face Inference API instead of local model."""
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": texts, "options": {"wait_for_model": True}}
    
    response = requests.post(EMBED_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"HF API Error: {response.text}")
    
    return np.array(response.json())


def _load_index(session_id: str):
    """Load stored chunks and embeddings for a session."""
    session_dir = f"data/sessions/{session_id}"
    chunk_path = os.path.join(session_dir, "chunks.pkl")
    emb_path = os.path.join(session_dir, "embeddings.pkl")
    if not os.path.exists(chunk_path) or not os.path.exists(emb_path):
        return None, None
    with open(chunk_path, "rb") as f:
        chunks = pickle.load(f)
    with open(emb_path, "rb") as f:
        embeddings = pickle.load(f)
    return chunks, embeddings


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a query vector and a matrix of vectors."""
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def _retrieve_top_chunks(question: str, chunks, embeddings, hf_token: str, top_k: int = 3) -> list[str]:
    """Encode question via API and return the top_k most relevant resume chunks."""
    query_vec = get_embeddings_from_api([question], hf_token)[0]
    scores = _cosine_similarity(query_vec, embeddings)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]


def _call_hf_api(prompt: str, hf_token: str) -> str:
    """Send a prompt to HF Router API (OpenAI-compatible) and return the generated text."""
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.3,
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

    if response.status_code == 503:
        return "⚠️ The AI model is loading. Please wait a moment and try again."
    if response.status_code == 401:
        return "❌ Invalid Hugging Face token. Please check your HF_TOKEN in the .env file."
    if not response.ok:
        return f"❌ HF API error {response.status_code}: {response.text}"

    result = response.json()
    if "choices" in result and result["choices"]:
        return result["choices"][0].get("message", {}).get("content", "").strip()
    return "⚠️ No response generated."


def query(session_id: str, question: str, hf_token: str) -> str:
    """
    Agentic RAG pipeline (Multi-Hop):
      1. Ask LLM to decompose question into sub-queries.
      2. Retrieve for sub-queries and pool chunks.
      3. Generate answer.
    """
    chunks, embeddings = _load_index(session_id)
    if chunks is None:
        return "⚠️ Please upload at least one resume to this session first."

    # 1. Decomposition prompt
    decomp_prompt = (
        "You are an AI assistant. Given this user question, generate exactly 2 short, distinct search queries "
        "that would help answer it if it requires multiple steps. If it is a simple question, return the same query twice. "
        "Return ONLY the queries separated by a pipe character (|) and nothing else.\n\n"
        f"Question: {question}"
    )
    
    decomp_resp = _call_hf_api(decomp_prompt, hf_token)
    subqueries = decomp_resp.split('|')
    if len(subqueries) < 2:
        subqueries = [question, question]
        
    combined_chunks = []
    for sq in subqueries:
        sq = sq.strip()
        if sq:
            result_chunks = _retrieve_top_chunks(sq, chunks, embeddings, hf_token, top_k=8)
            combined_chunks.extend(result_chunks)
            
    # Deduplicate while preserving order
    seen = set()
    final_chunks = []
    for c in combined_chunks:
        if c not in seen:
            seen.add(c)
            final_chunks.append(c)
            
    context = "\n\n---\n\n".join(final_chunks[:15])

    prompt = (
        "You are an expert HR assistant analyzing one or more candidate resumes. "
        "Your communication style should be conversational, professional, and highly structured, exactly like ChatGPT. "
        "Read the provided resume context thoroughly and answer the question comprehensively. "
        "Use Markdown formatting (bullet points, bold text, headers) to make your response easy to read. "
        "Extract ALL relevant information from the context. If multiple candidates are provided in the context, compare them accurately. "
        "IMPORTANT: Every snippet of context begins with a [Source: ...] tag indicating which document it belongs to. "
        "Use these tags to explicitly mention candidate names or file names when answering questions about who possesses specific skills. "
        "If the answer is not contained in the context, politely inform the user that the information is not available.\n\n"
        f"### Resume Context:\n{context}\n\n"
        f"### Question:\n{question}\n\n"
        "### Response:\n"
    )

    return _call_hf_api(prompt, hf_token)


def evaluate_fit(session_id: str, jd_text: str, hf_token: str) -> str:
    """Automated Contextual Fit Reasoning against a Job Description."""
    chunks, embeddings = _load_index(session_id)
    if chunks is None:
        return "⚠️ Please upload at least one resume to this session first."

    # Extract key skills from JD for better retrieval
    extract_prompt = (
        "Extract a list of the 3 most critical skills or requirements from this Job Description. "
        "Return ONLY those 3 items separated by commas.\n\n"
        f"Job Description: {jd_text}"
    )
    key_skills_resp = _call_hf_api(extract_prompt, hf_token)
    
    combined_chunks = []
    result_jd = _retrieve_top_chunks(jd_text, chunks, embeddings, hf_token, top_k=10)
    result_skills = _retrieve_top_chunks(key_skills_resp, chunks, embeddings, hf_token, top_k=10)
    
    combined_chunks.extend(result_jd)
    combined_chunks.extend(result_skills)
    
    seen = set()
    final_chunks = []
    for c in combined_chunks:
        if c not in seen:
            seen.add(c)
            final_chunks.append(c)
            
    context = "\n\n---\n\n".join(final_chunks[:20])

    prompt = (
        "You are an expert HR evaluator. You are given a Job Description and resume context for one or more candidates. "
        "For each candidate found in the context (identified by [Source: ...]), provide a structured evaluation "
        "comparing their profile against the Job Description. The evaluation must be objective and blind to demographic data (since names may be redacted).\n\n"
        "Use the EXACT formatting below for EACH candidate:\n"
        "### Candidate: [Source Name]\n"
        "**Overall Fit Summary:** (Brief 2 sentence summary)\n"
        "**✅ Pros:**\n"
        "- (Match 1)\n"
        "- (Match 2)\n"
        "**❌ Cons/Gaps:**\n"
        "- (Gap 1)\n"
        "**❓ Missing Information:**\n"
        "- (Info not explicitly found in context)\n\n"
        f"### Job Description:\n{jd_text}\n\n"
        f"### Candidate Context:\n{context}\n\n"
        "### Evaluation:\n"
    )

    return _call_hf_api(prompt, hf_token)


# ── CLI usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv("HF_TOKEN", "")
    if not token:
        print("❌ HF_TOKEN not set. Please add it to your .env file.")
        exit(1)

    while True:
        q = input("\nAsk a question (or type 'exit'): ").strip()
        if q.lower() == "exit":
            break
        session_id = input("Enter session ID: ").strip()
        print("\n💬 Answer:\n", query(session_id, q, token))
