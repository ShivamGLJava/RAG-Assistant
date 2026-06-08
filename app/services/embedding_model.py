import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
EMBEDDING_MODEL = "ibm-granite/granite-embedding-311m-multilingual-r2"

print("\n" + "="*70)
print("[INIT] HF Inference Client Configuration")
print("="*70)

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN not found in .env file!")
    print("[ERROR] This is REQUIRED to use HF Inference API")
    print("[ERROR] Please set HF_TOKEN in your .env file")
    print("[ERROR] Get your token from: https://huggingface.co/settings/tokens")
    raise ValueError("HF_TOKEN is required but not set in .env")

print(f"[OK] HF_TOKEN found in .env")
print(f"[OK] Token starts with: {HF_TOKEN[:20]}...")
print(f"[OK] Embedding model: {EMBEDDING_MODEL}")
print(f"[OK] Model description: IBM Granite 311M (multilingual embeddings)")

# Initialize client
try:
    client = InferenceClient(
        api_key=HF_TOKEN,
        provider="hf-inference",
    )
    print(f"[OK] InferenceClient initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize InferenceClient: {type(e).__name__}: {str(e)}")
    raise

# Test API connectivity on startup
print(f"\n[TESTING] Verifying HF Inference API connectivity...")
print(f"[TESTING] Generating test embedding...")
try:
    test_embedding = client.feature_extraction(
        "test",
        model=EMBEDDING_MODEL
    )
    print(f"[OK] HF Inference API connectivity test PASSED")
    print(f"[OK] Test embedding generated successfully")
    print(f"[OK] Embedding dimension: {len(test_embedding)}")
except Exception as e:
    error_str = str(e)
    print(f"[ERROR] Failed to connect to HF API")
    print(f"[ERROR] Error type: {type(e).__name__}")
    print(f"[ERROR] Details: {error_str[:300]}")

    if "getaddrinfo failed" in error_str or "Name or service not known" in error_str:
        print(f"[DIAG] DNS Resolution FAILED")
        print(f"[DIAG] Cannot reach api-inference.huggingface.co")
    elif "401" in error_str or "Unauthorized" in error_str:
        print(f"[DIAG] Unauthorized - Check your HF_TOKEN is valid")
    elif "403" in error_str or "Forbidden" in error_str:
        print(f"[DIAG] Forbidden - Check account permissions")
    elif "429" in error_str or "Rate limit" in error_str:
        print(f"[DIAG] Rate limited - Wait and retry later")

    raise

print("="*70 + "\n")


def generate_embedding(text: str) -> list:
    """
    Convert text into embedding vector using HF Inference Client.
    Uses ibm-granite/granite-embedding-311m-multilingual-r2 model.

    Args:
        text: Input text to embed

    Returns:
        Embedding vector (768 dimensions from Granite model)
    """
    try:
        
        embedding = client.feature_extraction(
            text,
            model=EMBEDDING_MODEL
        )

        # Convert numpy array to list if needed
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()

        if isinstance(embedding, list) and len(embedding) > 0:
            if isinstance(embedding[0], list):
                embedding = embedding[0]    

        if not isinstance(embedding, list) or len(embedding) == 0:
            raise ValueError(f"Unexpected embedding format: {type(embedding)}")

        return embedding

    except Exception as e:
        error_msg = f"Embedding generation failed: {type(e).__name__}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Full traceback:")
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg)


if __name__ == "__main__":
    sample_text = "What is AWS EC2?"
    print(f"\n[TEST] Testing embedding generation...")
    print(f"[TEST] Input: '{sample_text}'")

    embedding = generate_embedding(sample_text)
    print(f"[OK] Embedding generated successfully")
    print(f"[OK] Embedding dimension: {len(embedding)}")
    print(f"[OK] First 5 values: {embedding[:5]}")