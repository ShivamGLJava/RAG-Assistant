from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import os

class VectorStore:
    def __init__(self, collection_name: str = "enterprise_docs"):
        # Defaulting to local Qdrant instance
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def upsert_chunks(self, chunks: List[Dict[str, Any]], vectors: List[List[float]]):
        """
        Stores chunks and their vectors in Qdrant with full payload metadata.
        """
        points = [
            PointStruct(
                id=chunks[i]["id"],
                vector=vectors[i],
                payload={
                    "content": chunks[i]["content"],
                    **chunks[i]["metadata"]
                }
            )
            for i in range(len(chunks))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector: List[float], limit: int = 5, dept_filter: str = None) -> List[Dict[str, Any]]:
        """
        Performs semantic search with optional metadata filtering.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_filter = None
        if dept_filter:
            query_filter = Filter(
                must=[FieldCondition(key="department", match=MatchValue(value=dept_filter))]
            )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points
        return [
            {
                "id": hit.id,
                "score": hit.score if hasattr(hit, "score") else 1.0,
                "content": hit.payload["content"],
                "metadata": hit.payload
            }
            for hit in results
        ]
