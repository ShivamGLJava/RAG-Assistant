"""Main entry point for RAG Document Ingestion Pipeline and Application Server"""

import sys
from app.services.ingestion import IngestionEngine


def run_ingestion():
    """Execute document ingestion pipeline for FAQs.pdf and AWS.pdf"""
    engine = IngestionEngine()
    results = engine.ingest_documents()

    print("\n" + "=" * 70)
    print("📦 INGESTION COMPLETE - SUMMARY")
    print("=" * 70)

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
    if len(sys.argv) > 1 and sys.argv[1] == "--ingest":
        run_ingestion()
    else:
        print("\n" + "=" * 80)
        print("Cloud Infrastructure Auditing Engine - RAG Assistant")
        print("=" * 80 + "\n")
        print("To launch the FastAPI server, run:")
        print("\n  uvicorn app.main:app --reload\n")
        print("To run the document ingestion pipeline (FAQs.pdf, AWS.pdf), use:")
        print("\n  python main.py --ingest\n")
        print("=" * 80 + "\n")
