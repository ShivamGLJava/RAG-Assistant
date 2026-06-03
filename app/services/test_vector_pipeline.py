from app.services import IngestionEngine
from app.services.vector_search import index_chunks, semantic_search
from app.services.qdrant_store import initialize_collection

initialize_collection()

engine = IngestionEngine()
engine.ingest_documents()

chunks = engine.get_chunks("fixed")

print(f"\nIndexing {len(chunks)} chunks...")
index_chunks(chunks)

results = semantic_search(
    "What is Amazon S3?",
    department="Engineering"
)

print("\nSearch Results:\n")

for i, result in enumerate(results, start=1):

    print(f"\nResult {i}")
    print(f"Score: {result['score']:.4f}")

    print("\nAnswer:")
    print(result["content"])

    print(
        f"\nSource: {result['source_document']} | "
        f"Chunk: {result['chunk_id']}"
    )

    print("-" * 80)