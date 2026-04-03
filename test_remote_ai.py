import os
import sys
from dotenv import load_dotenv
import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())

import rag_query

load_dotenv()
token = os.getenv("HF_TOKEN")

if not token:
    print("❌ HF_TOKEN not found in .env")
    sys.exit(1)

try:
    test_texts = ["Hello world", "This is a test of the remote embedding API"]
    embeddings = rag_query.get_embeddings_from_api(test_texts, token)
    print(f"✅ Success! Received embeddings with shape: {embeddings.shape}")
    if embeddings.shape == (2, 384): # all-MiniLM-L6-v2 has 384 dims
        print("✅ Vector dimensions are correct.")
except Exception as e:
    print(f"❌ Error testing API: {e}")
