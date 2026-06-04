def compute_rrf(dense_results, sparse_results, k=10, top_n=3):
    """
    Reciprocal Rank Fusion (RRF) combines dense and sparse search results.

    Args:
        dense_results: List of dictionaries with chunk_id, text_content, metadata
        sparse_results: List of dictionaries with chunk_id, text_content, metadata
        k: RRF constant (default 10, adjusted for development to produce meaningful scores)
        top_n: Number of top results to return

    Returns:
        List of fused results with RRF scores, sorted by score descending
    """
    rrf_scores = {}

    for rank, result in enumerate(dense_results, start=1):
        chunk_id = result["chunk_id"]
        rrf_score = 1 / (k + rank)
        if chunk_id not in rrf_scores:
            rrf_scores[chunk_id] = {"score": 0, "data": result}
        rrf_scores[chunk_id]["score"] += rrf_score

    for rank, result in enumerate(sparse_results, start=1):
        chunk_id = result["chunk_id"]
        rrf_score = 1 / (k + rank)
        if chunk_id not in rrf_scores:
            rrf_scores[chunk_id] = {"score": 0, "data": result}
        rrf_scores[chunk_id]["score"] += rrf_score

    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:top_n]

    fused_candidates = []
    for rank, (chunk_id, item) in enumerate(sorted_results, start=1):
        fused_candidates.append({
            "Rank": rank,
            "Chunk ID": chunk_id,
            "Calculated RRF Score": round(item["score"], 4),
            "Source Document Name": item["data"].get("metadata", {}).get("source_document", item["data"].get("source_document", "unknown")),
            "text_content": item["data"].get("text_content", item["data"].get("content", ""))
        })

    return fused_candidates
