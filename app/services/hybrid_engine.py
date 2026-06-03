from typing import List, Dict, Any
from app.db.vector_store import VectorStore

class HybridEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.k = 60  # Standard RRF constant

    def rrf_fusion(self, vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Implementation of Reciprocal Rank Fusion (RRF).
        Scores documents based on their rank in both search lists.
        """
        scores = {}
        
        # Process Vector Results
        for rank, hit in enumerate(vector_results):
            doc_id = hit["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (self.k + rank + 1)
            # Store the hit data for later retrieval
            scores[f"{doc_id}_data"] = hit

        # Process Keyword Results
        for rank, hit in enumerate(keyword_results):
            doc_id = hit["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (self.k + rank + 1)
            # Ensure we have the hit data (prefer keyword hits if they differ in metadata)
            if f"{doc_id}_data" not in scores:
                scores[f"{doc_id}_data"] = hit

        # Sort by fused score
        fused_results = sorted(
            [
                {**scores[f"{doc_id}_data"], "rrf_score": score}
                for doc_id, score in scores.items()
                if not doc_id.endswith("_data")
            ],
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return fused_results

    async def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5, dept_filter: str = None) -> List[Dict[str, Any]]:
        """
        Executes parallel searches and fuses results.
        """
        # 1. Semantic Search (Qdrant)
        v_results = self.vector_store.search(query_vector, limit=limit, dept_filter=dept_filter)
        
        # 2. Keyword Search (Simulated Keyword Search logic)
        # Note: In a real system, this calls a PostgreSQL tsvector or BM25 index
        k_results = self._simulated_keyword_search(query, dept_filter)
        
        # 3. Fuse
        combined = self.rrf_fusion(v_results, k_results)
        
        return combined[:limit]

    def _simulated_keyword_search(self, query: str, dept_filter: str) -> List[Dict[str, Any]]:
        """
        A placeholder for logic that would query PostgreSQL's keyword indices.
        """
        # TODO: Implement actual SQL query for keywords
        return []
