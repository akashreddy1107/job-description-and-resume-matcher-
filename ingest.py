from pypdf import PdfReader
import docx
# from sentence_transformers import SentenceTransformer  <-- REMOVED to save 500MB
import rag_query  # Use remote embeddings instead
import os
import numpy as np
import re
import spacy

DATA_DIR = "data/sessions"
os.makedirs(DATA_DIR, exist_ok=True)

_model = None
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        print("[INFO] Loading Spacy NLP model...")
        try:
            _nlp = spacy.load("en_core_web_sm")
        except:
            print("[WARNING] Could not load en_core_web_sm. Anonymization of names will be disabled.")
            _nlp = False
    return _nlp

# Model loading removed - now use rag_query.get_embeddings_from_api


def anonymize_text(text):
    # Regex for Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    # Regex for Phones
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', text)
    
    nlp = get_nlp()
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Only replace if it's a likely name to avoid false positives
                if len(ent.text) > 2:
                    text = text.replace(ent.text, '[REDACTED_PERSON]')
    return text

def semantic_chunking(text, max_chunk_size=1500):
    # Split text by double newlines or basic layout boundaries
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def extract_text(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif file_path.endswith(".docx") or file_path.endswith(".doc"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    return text

def process_files(session_id, files_info, hf_token):
    """Refactored to use remote embeddings via Hugging Face API."""
    full_text = ""
    for f_info in files_info:
        file_path = f_info["file_path"]
        orig_name = f_info["filename"]
        text = extract_text(file_path)
        
        # Add source tag for multi-hop retrieval traceability
        full_text += f"\n\n[Source: {orig_name}]\n{text}"

    # 1. Blind RAG: Anonymize
    anonymized_text = anonymize_text(full_text)

    # 2. Semantic Chunking
    chunks = semantic_chunking(anonymized_text)
    if not chunks:
        return 0

    # 3. Remote Embeddings (Saves 500MB+ disk space)
    print(f"[INFO] Requesting embeddings for {len(chunks)} chunks via API...")
    embeddings = rag_query.get_embeddings_from_api(chunks, hf_token)
    
    # 4. Save
    session_dir = f"{DATA_DIR}/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    with open(f"{session_dir}/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
    with open(f"{session_dir}/embeddings.pkl", "wb") as f:
        pickle.dump(embeddings, f)
        
    print(f"[SUCCESS] Indexed {len(chunks)} chunks successfully!")
    return len(chunks)