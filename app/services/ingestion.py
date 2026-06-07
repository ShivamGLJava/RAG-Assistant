"""Document Ingestion Engine - Engineer 1 DI (Ingestion & Text Parsing Lead)"""

import os
import sys
from typing import List, Dict, Any

from .document_loader import DocumentLoader
from .chunking_strategies import FixedChunkingStrategy, SemanticChunkingStrategy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import DOCUMENTS, DEPARTMENT, FIXED_CHUNK_SIZE, FIXED_CHUNK_OVERLAP


class IngestionEngine:
    """Main document ingestion pipeline with both chunking strategies."""

    def __init__(self, chunk_size: int = FIXED_CHUNK_SIZE, chunk_overlap: int = FIXED_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.fixed_chunker = FixedChunkingStrategy(chunk_size, chunk_overlap)
        self.semantic_chunker = SemanticChunkingStrategy(similarity_threshold=0.5)
        self.fixed_chunks = []
        self.semantic_chunks = []

    def ingest_documents(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Load and chunk all documents using both strategies.

        Returns:
        {
            "fixed": {
                "aws": [chunks...],
                "faqs": [chunks...]
            },
            "semantic": {
                "aws": [chunks...],
                "faqs": [chunks...]
            }
        }
        """
        results = {
            "fixed": {},
            "semantic": {}
        }

        for doc_name, doc_path in DOCUMENTS.items():
            if not os.path.exists(doc_path):
                print(f"[ERROR] Document not found: {doc_path}")
                continue

            print(f"\n[DOC] Processing {doc_name.upper()}: {doc_path}")

            # Load document
            loader = DocumentLoader(doc_path)
            text = loader.extract_text()
            loader.close()

            print(f"   [OK] Extracted {len(text)} characters")

            # Fixed-size chunking
            print(f"\n   [FIXED] FIXED-SIZE CHUNKING")
            fixed_chunks = self.fixed_chunker.chunk(text, doc_path, DEPARTMENT)
            results["fixed"][doc_name] = fixed_chunks
            self.fixed_chunks.extend(fixed_chunks)
            print(f"      [OK] Created {len(fixed_chunks)} chunks")
            self._print_chunk_stats(fixed_chunks)

            # Semantic chunking
            print(f"\n   [SEMANTIC] SEMANTIC CHUNKING")
            semantic_chunks = self.semantic_chunker.chunk(text, doc_path, DEPARTMENT)
            results["semantic"][doc_name] = semantic_chunks
            self.semantic_chunks.extend(semantic_chunks)
            print(f"      [OK] Created {len(semantic_chunks)} chunks")
            self._print_chunk_stats(semantic_chunks)

            # Comparison
            self._compare_strategies(doc_name, fixed_chunks, semantic_chunks)

        return results

    def _print_chunk_stats(self, chunks: List[Dict[str, Any]]):
        """Print statistics about chunks."""
        if not chunks:
            return

        sizes = [c["chunk_size"] for c in chunks]
        word_counts = [len(c["content"].split()) for c in chunks]

        avg_size = sum(sizes) / len(sizes) if sizes else 0
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

        print(f"      • Avg size: {avg_size:.0f} chars (min: {min(sizes)}, max: {max(sizes)})")
        print(f"      • Avg words: {avg_words:.0f} words/chunk")

    def _compare_strategies(self, doc_name: str, fixed: List[Dict], semantic: List[Dict]):
        """Compare fixed vs semantic chunking strategies."""
        print(f"\n   [STATS] COMPARISON ({doc_name.upper()})")

        fixed_total_size = sum(c["chunk_size"] for c in fixed)
        semantic_total_size = sum(c["chunk_size"] for c in semantic)
        fixed_avg_size = fixed_total_size / len(fixed) if fixed else 0
        semantic_avg_size = semantic_total_size / len(semantic) if semantic else 0

        print(f"      Fixed:    {len(fixed):3d} chunks | Avg size: {fixed_avg_size:6.0f} chars")
        print(f"      Semantic: {len(semantic):3d} chunks | Avg size: {semantic_avg_size:6.0f} chars")
        print(f"      Diff:     {len(fixed) - len(semantic):+3d} chunks | Size diff: {fixed_avg_size - semantic_avg_size:+6.0f} chars")

    def get_chunks(self, strategy: str = "semantic") -> List[Dict[str, Any]]:
        """Get all chunks for specified strategy. Defaults to semantic (RAGAS: 0.926)."""
        if strategy == "fixed":
            return self.fixed_chunks
        elif strategy == "semantic":
            return self.semantic_chunks
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def get_chunks_by_document(self, strategy: str, doc_name: str) -> List[Dict[str, Any]]:
        """Get chunks for specific document and strategy."""
        chunks = self.get_chunks(strategy)
        return [c for c in chunks if doc_name.lower() in c["source_document"].lower()]

    def save_to_qdrant(self):
        """Save chunks to Qdrant vector database."""
        try:
            from .qdrant_store import client, initialize_collection, COLLECTION_NAME
            from .embedding_model import generate_embedding

            # Initialize collection
            initialize_collection()

            # Get all chunks (using semantic strategy - better RAGAS score: 0.926)
            all_chunks = self.semantic_chunks

            if not all_chunks:
                print("[ERROR] No chunks to save!")
                return

            # Get embeddings for all chunks
            print(f"\n[EMBED] Generating embeddings for {len(all_chunks)} chunks...")
            embeddings = [generate_embedding(c["content"]) for c in all_chunks]

            # Prepare points for Qdrant
            points = []
            for idx, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
                points.append({
                    "id": idx + 1,
                    "vector": embedding,
                    "payload": {
                        "content": chunk["content"],
                        "source_document": chunk["source_document"],
                        "department": chunk["department"],
                        "chunk_id": chunk["chunk_id"],
                        "strategy": chunk["strategy"]
                    }
                })

            # Upsert to Qdrant
            print(f"[UPLOAD] Uploading {len(points)} points to Qdrant...")
            from qdrant_client.models import PointStruct

            qdrant_points = [
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"]
                )
                for p in points
            ]

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=qdrant_points
            )

            print(f"[OK] Successfully saved {len(points)} chunks to Qdrant!")

        except Exception as e:
            print(f"[ERROR] Error saving to Qdrant: {e}")
