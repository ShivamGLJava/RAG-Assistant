"""Main entry point for RAG Document Ingestion Pipeline"""

from app.services import IngestionEngine


def main():
    """Run the ingestion pipeline with both chunking strategies."""
    engine = IngestionEngine()
    results = engine.ingest_documents()

    print("\n" + "="*70)
    print("📦 INGESTION COMPLETE - SUMMARY")
    print("="*70)

    print("\nFIXED-SIZE STRATEGY:")
    fixed_total = 0
    for doc_name, chunks in results["fixed"].items():
        fixed_total += len(chunks)
        print(f"  {doc_name.upper()}: {len(chunks)} chunks")
    print(f"  TOTAL: {fixed_total} chunks")

    print("\nSEMANTIC STRATEGY:")
    semantic_total = 0
    for doc_name, chunks in results["semantic"].items():
        semantic_total += len(chunks)
        print(f"  {doc_name.upper()}: {len(chunks)} chunks")
    print(f"  TOTAL: {semantic_total} chunks")

    print(f"\n✅ Both strategies ready for Engineer 2 (Qdrant Vector Storage)")
    print(f"📝 Chunks will be compared using RAGAS metrics in later stages")


if __name__ == "__main__":
    main()
