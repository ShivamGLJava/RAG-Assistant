from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Model loaded")


def generate_embedding(text: str):
    """
    Convert text into a 384-dimensional vector.
    """
    return model.encode(text).tolist()


if __name__ == "__main__":

    sample_text = "CrashLoopBackOff troubleshooting"

    embedding = generate_embedding(sample_text)

    print("Embedding length:", len(embedding))