"""
Verify that we're actually using REAL chunks, not mock data
Shows chunk quality and retrieval in detail
"""

from app.services.ingestion import IngestionEngine
from app.services.embedding_model import generate_embedding
import numpy as np


def verify_ingestion():
    """Verify chunks are created from actual PDFs"""
    print("\n" + "="*70)
    print("STEP 1: VERIFY INGESTION - ARE CHUNKS REAL?")
    print("="*70)

    engine = IngestionEngine()
    results = engine.ingest_documents()

    # Check Fixed chunks
    fixed_chunks = []
    for doc_name, chunks in results.get("fixed", {}).items():
        print(f"\n✓ {doc_name.upper()}: {len(chunks)} fixed chunks created")
        for i, chunk in enumerate(chunks[:2]):  # Show first 2
            print(f"\n  Chunk {i+1}:")
            print(f"    Source: {chunk.get('source_document')}")
            print(f"    Size: {chunk.get('chunk_size')} chars")
            print(f"    Content preview: {chunk.get('content', '')[:100]}...")
        fixed_chunks.extend(chunks)

    print(f"\n📊 FIXED CHUNKS SUMMARY:")
    print(f"   Total: {len(fixed_chunks)}")
    print(f"   Avg size: {sum(c['chunk_size'] for c in fixed_chunks) / len(fixed_chunks):.0f} chars")
    print(f"   Min size: {min(c['chunk_size'] for c in fixed_chunks)} chars")
    print(f"   Max size: {max(c['chunk_size'] for c in fixed_chunks)} chars")

    return fixed_chunks


def verify_embedding():
    """Verify embeddings are working"""
    print("\n" + "="*70)
    print("STEP 2: VERIFY EMBEDDINGS")
    print("="*70)

    test_text = "AWS EC2 is a compute service"
    embedding = generate_embedding(test_text)

    print(f"✓ Embedding generated")
    print(f"   Text: '{test_text}'")
    print(f"   Embedding dimension: {len(embedding)}")
    print(f"   Embedding sample values: {embedding[:5]}")
    print(f"   Norm: {np.linalg.norm(embedding):.2f}")

    return embedding


def verify_retrieval(chunks):
    """Verify chunks are actually retrieved (not mocks)"""
    print("\n" + "="*70)
    print("STEP 3: VERIFY RETRIEVAL - ARE WE GETTING REAL CHUNKS?")
    print("="*70)

    query = "What is AWS EC2?"
    print(f"\nQuery: '{query}'")

    # Get query embedding
    query_embedding = generate_embedding(query)

    # Score all chunks
    scored_chunks = []
    for chunk in chunks:
        chunk_embedding = generate_embedding(chunk.get("content", ""))

        dot_product = np.dot(query_embedding, chunk_embedding)
        norm_q = np.linalg.norm(query_embedding)
        norm_c = np.linalg.norm(chunk_embedding)

        if norm_q > 0 and norm_c > 0:
            similarity = dot_product / (norm_q * norm_c)
        else:
            similarity = 0.0

        scored_chunks.append({
            **chunk,
            "similarity_score": similarity
        })

    # Sort by score
    scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Show top results
    print(f"\n✓ Retrieved top 5 chunks (out of {len(chunks)} total):")
    for i, chunk in enumerate(scored_chunks[:5], 1):
        print(f"\n  Rank {i}:")
        print(f"    Similarity Score: {chunk['similarity_score']:.4f}")
        print(f"    Source: {chunk.get('source_document')}")
        print(f"    Size: {chunk.get('chunk_size')} chars")
        print(f"    Content: {chunk.get('content', '')[:80]}...")

    # Statistics
    all_scores = [c["similarity_score"] for c in scored_chunks]
    print(f"\n📊 RETRIEVAL STATISTICS:")
    print(f"   Average similarity: {np.mean(all_scores):.4f}")
    print(f"   Max similarity: {np.max(all_scores):.4f}")
    print(f"   Min similarity: {np.min(all_scores):.4f}")
    print(f"   Median similarity: {np.median(all_scores):.4f}")

    # Check if top results are good
    top_3_avg = np.mean([c["similarity_score"] for c in scored_chunks[:3]])
    print(f"   Top 3 avg similarity: {top_3_avg:.4f}")

    if top_3_avg > 0.7:
        print(f"   ✓ GOOD: Top chunks have high relevance")
    elif top_3_avg > 0.5:
        print(f"   ⚠️  FAIR: Top chunks have moderate relevance")
    else:
        print(f"   ❌ POOR: Top chunks have low relevance")

    return scored_chunks


def check_chunk_quality(chunks):
    """Check if chunks are good quality (not empty, not too small)"""
    print("\n" + "="*70)
    print("STEP 4: CHECK CHUNK QUALITY")
    print("="*70)

    empty_chunks = [c for c in chunks if len(c.get("content", "").strip()) == 0]
    tiny_chunks = [c for c in chunks if len(c.get("content", "")) < 50]
    normal_chunks = [c for c in chunks if 50 <= len(c.get("content", "")) <= 1000]
    large_chunks = [c for c in chunks if len(c.get("content", "")) > 1000]

    print(f"\n✓ Chunk Quality Distribution:")
    print(f"   Empty chunks: {len(empty_chunks)} (BAD)")
    print(f"   Tiny chunks (<50 chars): {len(tiny_chunks)} (ACCEPTABLE)")
    print(f"   Normal chunks (50-1000 chars): {len(normal_chunks)} (GOOD)")
    print(f"   Large chunks (>1000 chars): {len(large_chunks)} (OK)")

    quality_score = (len(normal_chunks) + len(large_chunks) * 0.9) / len(chunks) * 100

    print(f"\n   Overall Quality Score: {quality_score:.1f}%")

    if quality_score > 80:
        print(f"   ✓ GOOD QUALITY CHUNKS")
    elif quality_score > 60:
        print(f"   ⚠️  MODERATE QUALITY CHUNKS")
    else:
        print(f"   ❌ POOR QUALITY CHUNKS - may need better chunking")

    # Show some examples
    if empty_chunks:
        print(f"\n   Example empty chunk:")
        print(f"     '{empty_chunks[0].get('content')}'")

    if normal_chunks:
        print(f"\n   Example good chunk:")
        print(f"     '{normal_chunks[0].get('content')[:100]}...'")


def main():
    """Run all verifications"""
    print("\n" + "="*70)
    print("🔍 CHUNK & RETRIEVAL VERIFICATION")
    print("="*70)
    print("This script verifies:")
    print("1. Chunks are created from REAL PDFs (not mock)")
    print("2. Embeddings are working properly")
    print("3. Real chunks are being retrieved")
    print("4. Chunk quality is good")

    # Run all checks
    chunks = verify_ingestion()
    verify_embedding()
    scored_chunks = verify_retrieval(chunks)
    check_chunk_quality(chunks)

    # Final verdict
    print("\n" + "="*70)
    print("✅ FINAL VERDICT")
    print("="*70)
    print("\nIf all checks passed:")
    print("  ✓ We ARE using REAL chunks from PDFs")
    print("  ✓ Embeddings are working")
    print("  ✓ Retrieval is returning real data")
    print("  ✓ Chunk quality is good")
    print("\nIf some checks failed:")
    print("  ❌ There might be an issue with chunking/retrieval")
    print("  ❌ The low evaluation scores might be due to chunk quality")


if __name__ == "__main__":
    main()
