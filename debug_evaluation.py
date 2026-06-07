"""
Debug Evaluation Script
Shows what chunks are being retrieved and what answers are generated
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from app.services.ingestion import IngestionEngine
from app.services.embedding_model import generate_embedding


load_dotenv()

TEST_QUERIES = [
    "What is AWS EC2?",
    "How do I fix a 502 error?",
]


def create_chunks():
    """Create chunks using both strategies"""
    print("\n" + "="*70)
    print("CREATING CHUNKS")
    print("="*70)

    engine = IngestionEngine()
    results = engine.ingest_documents()

    fixed_chunks = []
    for doc_chunks in results.get("fixed", {}).values():
        fixed_chunks.extend(doc_chunks)

    print(f"✓ Total fixed chunks: {len(fixed_chunks)}")
    return fixed_chunks


def retrieve_relevant_chunks(query: str, chunks, top_k: int = 3):
    """Retrieve chunks and show details"""
    try:
        query_embedding = generate_embedding(query)

        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = generate_embedding(chunk.get("content", ""))

            import numpy as np
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

        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]
    except Exception as e:
        print(f"Error: {e}")
        return []


async def generate_answer(query: str, chunks):
    """Generate answer and show details"""
    if not chunks:
        return "No chunks found"

    context = "\n\n".join([
        f"Chunk {i}: {chunk.get('content', '')}"
        for i, chunk in enumerate(chunks[:3])
    ])

    try:
        from app.services.orchestration import _get_client

        client = _get_client()
        prompt = f"""Answer the question using ONLY the provided context.

Context:
{context}

Question: {query}

Answer:"""

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


async def debug_evaluation():
    """Debug evaluation"""
    print("\n" + "="*70)
    print("🔍 DEBUG EVALUATION")
    print("="*70)

    chunks = create_chunks()

    for query in TEST_QUERIES:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"{'='*70}")

        # Get retrieved chunks
        retrieved = retrieve_relevant_chunks(query, chunks, top_k=3)

        print(f"\n📦 Retrieved {len(retrieved)} chunks:")
        for i, chunk in enumerate(retrieved, 1):
            print(f"\n  Chunk {i}:")
            print(f"    Similarity: {chunk.get('similarity_score', 0):.3f}")
            print(f"    Source: {chunk.get('source_document', 'Unknown')}")
            print(f"    Content: {chunk.get('content', '')[:150]}...")

        # Generate answer
        print(f"\n🤖 Generating answer...")
        answer = await generate_answer(query, retrieved)

        print(f"\n📝 Answer:")
        print(f"  {answer}")

        # Check answer quality
        if "Error" in answer:
            print("  ⚠️  Error in answer generation!")
        elif len(answer) < 20:
            print("  ⚠️  Answer too short!")
        else:
            print("  ✓ Answer generated")


if __name__ == "__main__":
    asyncio.run(debug_evaluation())
