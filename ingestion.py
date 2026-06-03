"""Document Ingestion Engine - Engineer 1 DI (Ingestion & Text Parsing Lead)"""

import os
from typing import List, Dict, Any
from document_loader import DocumentLoader
from chunking_strategies import FixedChunkingStrategy
from config import DOCUMENTS, DEPARTMENT, FIXED_CHUNK_SIZE, FIXED_CHUNK_OVERLAP


class IngestionEngine:
    """Main document ingestion pipeline with fixed-size chunking."""

    def __init__(self, chunk_size: int = FIXED_CHUNK_SIZE, chunk_overlap: int = FIXED_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunker = FixedChunkingStrategy(chunk_size, chunk_overlap)
        self.chunks = []

    def ingest_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load and chunk all documents from config.

        Returns:
        {
            "aws": [chunks...],
            "faqs": [chunks...]
        }
        """
        results = {}

        for doc_name, doc_path in DOCUMENTS.items():
            if not os.path.exists(doc_path):
                print(f"❌ Document not found: {doc_path}")
                continue

            print(f"\n📄 Processing {doc_name.upper()}: {doc_path}")

            # Load document
            loader = DocumentLoader(doc_path)
            text = loader.extract_text()
            loader.close()

            print(f"   ✓ Extracted {len(text)} characters")

            # Chunk document
            chunks = self.chunker.chunk(text, doc_path, DEPARTMENT)
            results[doc_name] = chunks
            self.chunks.extend(chunks)

            print(f"   ✓ Created {len(chunks)} chunks (size: {self.chunk_size}, overlap: {self.chunk_overlap})")
            self._print_chunk_stats(chunks)

        return results

    def _print_chunk_stats(self, chunks: List[Dict[str, Any]]):
        """Print statistics about chunks."""
        sizes = [c["chunk_size"] for c in chunks]
        word_counts = [len(c["content"].split()) for c in chunks]

        print(f"   • Avg chunk size: {sum(sizes) / len(sizes):.0f} chars (min: {min(sizes)}, max: {max(sizes)})")
        print(f"   • Avg words/chunk: {sum(word_counts) / len(word_counts):.0f} words")

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Get all ingested chunks."""
        return self.chunks

    def get_chunks_by_document(self, doc_name: str) -> List[Dict[str, Any]]:
        """Get chunks for specific document."""
        return [c for c in self.chunks if doc_name.lower() in c["source_document"].lower()]


if __name__ == "__main__":
    engine = IngestionEngine()
    results = engine.ingest_documents()

    print("\n" + "="*60)
    print("📦 INGESTION SUMMARY")
    print("="*60)

    total_chunks = 0
    for doc_name, chunks in results.items():
        total_chunks += len(chunks)
        print(f"{doc_name.upper()}: {len(chunks)} chunks")

    print(f"\nTotal: {total_chunks} chunks ready for vector indexing")
    print("✓ Ready for Engineer 2 (Qdrant Vector Storage)")
