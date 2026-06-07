"""
RAGAS Evaluation: Compare Fixed-Size vs Semantic Chunking Strategies

This script:
1. Creates chunks using both strategies
2. Retrieves relevant chunks for test queries
3. Generates answers using both chunk sets
4. Evaluates using RAGAS-like metrics
5. Provides comparison report
"""

import asyncio
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from app.services.ingestion import IngestionEngine
from app.services.embedding_model import generate_embedding


# Load environment variables
load_dotenv()

# Test queries for evaluation - AWS & Interview focused
TEST_QUERIES = [
    "What is Amazon EC2 and what are its key features?",
    "Explain the difference between EBS and S3 storage in AWS",
    "What is an AWS VPC and why is it important?",
    "How does AWS Auto Scaling work?",
    "What are the different types of AWS EC2 instances?",
    "Explain AWS Lambda and its use cases",
    "What is CloudFront and how does it improve performance?",
    "How does RDS differ from DynamoDB in AWS?"
]


def create_chunks():
    """Create chunks using both strategies"""
    print("\n" + "="*70)
    print("STEP 1: CREATING CHUNKS")
    print("="*70)

    engine = IngestionEngine()
    results = engine.ingest_documents()

    fixed_chunks = []
    semantic_chunks = []

    for doc_chunks in results.get("fixed", {}).values():
        fixed_chunks.extend(doc_chunks)

    for doc_chunks in results.get("semantic", {}).values():
        semantic_chunks.extend(doc_chunks)

    print(f"[OK] Fixed-size chunks: {len(fixed_chunks)}")
    print(f"[OK] Semantic chunks: {len(semantic_chunks)}")

    return fixed_chunks, semantic_chunks


def retrieve_relevant_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Retrieve top-k relevant chunks for a query using vector similarity"""
    try:
        query_embedding = generate_embedding(query)

        # Calculate similarity scores
        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = generate_embedding(chunk.get("content", ""))

            # Cosine similarity
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

        # Sort and return top-k
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]
    except Exception as e:
        print(f"Error in retrieval: {e}")
        return []


async def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Generate answer using retrieved chunks with Gemini"""
    if not chunks:
        return "No relevant information found."

    context = "\n\n".join([
        f"• {chunk.get('content', '')}"
        for chunk in chunks[:3]
    ])

    try:
        from app.services.orchestration import _get_client

        client = _get_client()
        prompt = f"""Answer the following question using ONLY the provided context. Be concise.

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
        return f"[Error: {str(e)}]"


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts"""
    try:
        from app.services.embedding_model import generate_embedding
        import numpy as np

        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)

        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 > 0 and norm2 > 0:
            return dot_product / (norm1 * norm2)
        return 0.0
    except:
        return 0.0


async def evaluate_strategy(
    strategy_name: str,
    chunks: List[Dict[str, Any]],
    queries: List[str]
) -> Dict[str, Any]:
    """Evaluate a chunking strategy using RAGAS-like metrics"""
    print(f"\n{'='*70}")
    print(f"EVALUATING: {strategy_name}")
    print(f"{'='*70}")

    results = []

    for query in queries:
        print(f"\n[Q] Query: {query}")

        # Retrieve relevant chunks
        retrieved = retrieve_relevant_chunks(query, chunks, top_k=3)

        if not retrieved:
            print("  [WARN] No chunks retrieved")
            continue

        # Generate answer
        print("  [AI] Generating answer...")
        answer = await generate_answer(query, retrieved)

        # Calculate metrics
        context_text = "\n".join([c.get("content", "") for c in retrieved])

        # RAGAS-like metrics:
        # 1. Answer Relevancy: How relevant is answer to query
        answer_relevancy = calculate_similarity(query, answer)

        # 2. Context Relevancy: How relevant is context to query
        context_relevancy = calculate_similarity(query, context_text)

        # 3. Context Precision: Average similarity score of retrieved chunks
        # RAGAS Definition: Proportion of retrieved contexts that are relevant to the query
        # Using average similarity as the metric
        if retrieved:
            context_precision = sum(c.get("similarity_score", 0) for c in retrieved) / len(retrieved)
        else:
            context_precision = 0

        # 4. Faithfulness: How faithful is answer to context (simplified)
        faithfulness = calculate_similarity(answer, context_text)

        result = {
            "query": query,
            "answer": answer[:100] + "..." if len(answer) > 100 else answer,
            "chunks_retrieved": len(retrieved),
            "answer_relevancy": answer_relevancy,
            "context_relevancy": context_relevancy,
            "context_precision": context_precision,
            "faithfulness": faithfulness,
            "avg_score": (answer_relevancy + context_relevancy + context_precision + faithfulness) / 4
        }

        results.append(result)

        print(f"  [OK] Answer Relevancy: {result['answer_relevancy']:.3f}")
        print(f"  [OK] Context Relevancy: {result['context_relevancy']:.3f}")
        print(f"  [OK] Context Precision: {result['context_precision']:.3f}")
        print(f"  [OK] Faithfulness: {result['faithfulness']:.3f}")
        print(f"  [OK] Average Score: {result['avg_score']:.3f}")

    if not results:
        print(f"  [WARN] No results for {strategy_name}")
        return {
            "strategy": strategy_name,
            "results": [],
            "avg_answer_relevancy": 0,
            "avg_context_relevancy": 0,
            "avg_context_precision": 0,
            "avg_faithfulness": 0,
            "overall_score": 0
        }

    return {
        "strategy": strategy_name,
        "results": results,
        "avg_answer_relevancy": sum(r["answer_relevancy"] for r in results) / len(results),
        "avg_context_relevancy": sum(r["context_relevancy"] for r in results) / len(results),
        "avg_context_precision": sum(r["context_precision"] for r in results) / len(results),
        "avg_faithfulness": sum(r["faithfulness"] for r in results) / len(results),
        "overall_score": sum(r["avg_score"] for r in results) / len(results)
    }


async def run_evaluation():
    """Run complete evaluation"""
    print("\n" + "="*70)
    print("[EVAL] RAGAS EVALUATION: FIXED vs SEMANTIC CHUNKING")
    print("="*70)

    # Step 1: Create chunks
    fixed_chunks, semantic_chunks = create_chunks()

    # Step 2: Evaluate both strategies
    print("\n" + "="*70)
    print("STEP 2: RAGAS EVALUATION")
    print("="*70)

    fixed_results = await evaluate_strategy("FIXED-SIZE", fixed_chunks, TEST_QUERIES)
    semantic_results = await evaluate_strategy("SEMANTIC", semantic_chunks, TEST_QUERIES)

    # Step 3: Comparison Report
    print("\n" + "="*70)
    print("[REPORT] COMPARISON REPORT")
    print("="*70)

    metrics = ["answer_relevancy", "context_relevancy", "context_precision", "faithfulness"]

    print(f"\n{'Metric':<25} {'Fixed-Size':<15} {'Semantic':<15} {'Winner':<15}")
    print("-" * 70)

    for metric in metrics:
        fixed_val = fixed_results[f"avg_{metric}"]
        semantic_val = semantic_results[f"avg_{metric}"]
        winner = "FIXED [OK]" if fixed_val > semantic_val else "SEMANTIC [OK]"

        print(f"{metric:<25} {fixed_val:<15.3f} {semantic_val:<15.3f} {winner:<15}")

    # Overall score (special case)
    fixed_overall = fixed_results["overall_score"]
    semantic_overall = semantic_results["overall_score"]
    winner = "FIXED [OK]" if fixed_overall > semantic_overall else "SEMANTIC [OK]"
    print(f"{'overall_score':<25} {fixed_overall:<15.3f} {semantic_overall:<15.3f} {winner:<15}")

    # Final recommendation
    print("\n" + "="*70)
    print("[RECOMMEND] RECOMMENDATION")
    print("="*70)

    if fixed_results["overall_score"] > semantic_results["overall_score"]:
        print(f"\n[WIN] FIXED-SIZE CHUNKING WINS!")
        print(f"   Fixed Score: {fixed_results['overall_score']:.3f}")
        print(f"   Semantic Score: {semantic_results['overall_score']:.3f}")
        print(f"   Better by: {(fixed_results['overall_score'] - semantic_results['overall_score'])*100:.1f}%")
        print(f"\n[TIP] Use FIXED-SIZE chunks in production")
    else:
        print(f"\n[WIN] SEMANTIC CHUNKING WINS!")
        print(f"   Semantic Score: {semantic_results['overall_score']:.3f}")
        print(f"   Fixed Score: {fixed_results['overall_score']:.3f}")
        print(f"   Better by: {(semantic_results['overall_score'] - fixed_results['overall_score'])*100:.1f}%")
        print(f"\n[TIP] Use SEMANTIC chunks in production")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
