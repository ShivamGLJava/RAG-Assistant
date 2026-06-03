from app.services.lexical_search import keyword_search
from app.services.rrf_fusion import compute_rrf


def main():
    # Dense mock data aligned dynamically
    dense_mock_results = [
        {
            "chunk_id": "doc_002_chk_3",
            "Chunk ID": "doc_002_chk_3",
            "text_content": "Container CrashLoopBackOff occurs when your pod fails to start. Check logs with kubectl logs.",
            "metadata": {"source_document": "kubernetes_handbook.md", "source": "kubernetes_handbook.md"}
        },
        {
            "chunk_id": "doc_004_chk_1",
            "Chunk ID": "doc_004_chk_1",
            "text_content": "Kubernetes debugging: inspect pod status and resource limits to resolve CrashLoopBackOff.",
            "metadata": {"source_document": "k8s_debugging.md", "source": "k8s_debugging.md"}
        },
        {
            "chunk_id": "doc_001_chk_1",
            "Chunk ID": "doc_001_chk_1",
            "text_content": "To fix a 502 Bad Gateway error, check your upstream server status and verify network connectivity.",
            "metadata": {"source_document": "troubleshooting_guide.md", "source": "troubleshooting_guide.md"}
        },
        {
            "chunk_id": "doc_005_chk_2",
            "Chunk ID": "doc_005_chk_2",
            "text_content": "HTTP status codes: 502 Bad Gateway means upstream service unavailable or misconfigured.",
            "metadata": {"source_document": "http_reference.md", "source": "http_reference.md"}
        }
    ]

    user_query = "How do I fix a 502 error and container CrashLoopBackOff anomalies?"

    print(f"User Query: {user_query}\n")
    print("=" * 80)

    # 1. Sparse / Lexical Run
    sparse_results = keyword_search(user_query)
    print(f"Lexical Search Results ({len(sparse_results)} found):")
    for i, result in enumerate(sparse_results, start=1):
        c_id = result.get("chunk_id", result.get("Chunk ID", "N/A"))
        meta = result.get("metadata", {})
        doc_name = meta.get("source_document", meta.get("source", "Unknown"))
        print(f"  {i}. Chunk {c_id}: {doc_name}")

    print("\n" + "=" * 80)
    print(f"Dense Vector Search Results ({len(dense_mock_results)} mocked):")
    for i, result in enumerate(dense_mock_results, start=1):
        c_id = result.get("chunk_id", result.get("Chunk ID", "N/A"))
        meta = result.get("metadata", {})
        doc_name = meta.get("source_document", meta.get("source", "Unknown"))
        print(f"  {i}. Chunk {c_id}: {doc_name}")

    print("\n" + "=" * 80)
    print("RRF Fusion (k=60, top_n=3):")
    print("=" * 80 + "\n")

    # 2. Compute Fusion Blending
    fused_results = compute_rrf(dense_mock_results, sparse_results, k=60, top_n=3)

    # 3. Print Results Safely handling both Lowercase and Uppercase backends
    for rank, candidate in enumerate(fused_results, start=1):
        c_id = candidate.get("chunk_id", candidate.get("Chunk ID", "N/A"))
        score = candidate.get("rrf_score", candidate.get("Calculated RRF Score", 0.0))
        meta = candidate.get("metadata", {})
        doc_name = meta.get("source_document", meta.get("source", candidate.get("Source Document Name", "Unknown")))
        
        print(f"Rank: {rank}")
        print(f"Chunk ID: {c_id}")
        print(f"Calculated RRF Score: {score}")
        print(f"Source Document Name: {doc_name}")
        print("-" * 80)


if __name__ == "__main__":
    main()