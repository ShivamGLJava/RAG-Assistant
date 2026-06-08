from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from .embedding_model import generate_embedding
from .qdrant_store import (
    client,
    COLLECTION_NAME,
    initialize_collection
)


def index_chunks(chunks):

    points = []

    for idx, chunk in enumerate(chunks):

        vector = generate_embedding(
            chunk["content"]
        )

        points.append(
            PointStruct(
                id=idx,
                vector=vector,
                payload={
                    "content": chunk["content"],
                    "source_document": chunk["source_document"],
                    "department": chunk["department"],
                    "chunk_id": chunk["chunk_id"],
                    "chunk_size": chunk["chunk_size"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Indexed {len(points)} chunks")


def semantic_search(
    query: str,
    limit: int = 10,
    department: str = None,
    source_document: str = None
):

    initialize_collection()
    query_vector = generate_embedding(query)
    
    print(f"[VECTOR_SEARCH] Query vector type: {type(query_vector)}")
    print(f"[VECTOR_SEARCH] Query vector length: {len(query_vector)}")
    if len(query_vector) > 0:
        print(f"[VECTOR_SEARCH] First element type: {type(query_vector[0])}")
        print(f"[VECTOR_SEARCH] First 3 values: {query_vector[:3]}")

    conditions = []

    if department:
        conditions.append(
            FieldCondition(
                key="department",
                match=MatchValue(value=department)
            )
        )

    if source_document:
        conditions.append(
            FieldCondition(
                key="source_document",
                match=MatchValue(value=source_document)
            )
        )

    search_filter = None

    if conditions:
        search_filter = Filter(
            must=conditions
        )

    print(f"[VECTOR_SEARCH] About to query Qdrant...")
    print(f"[VECTOR_SEARCH] Collection: {COLLECTION_NAME}")
    print(f"[VECTOR_SEARCH] Query vector length: {len(query_vector)}")
    print(f"[VECTOR_SEARCH] Search filter: {search_filter}")

    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=search_filter,
            limit=limit
        )
        print(f"[VECTOR_SEARCH] Qdrant query succeeded! Found {len(results.points)} points")
    except Exception as e:
        print(f"[VECTOR_SEARCH] Qdrant query FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    output = []

    for point in results.points:

        output.append(
            {
                "score": point.score,
                "content": point.payload["content"],
                "source_document": point.payload["source_document"],
                "department": point.payload["department"],
                "chunk_id": point.payload["chunk_id"],
                "chunk_size": point.payload.get("chunk_size", 0)
            }
        )

    return output


if __name__ == "__main__":

    initialize_collection()

    sample_chunks = [
        {
            "content":
            "CrashLoopBackOff occurs when a container repeatedly fails to start.",

            "source_document":
            "kubernetes.pdf",

            "department":
            "Engineering",

            "chunk_id":
            0,

            "chunk_size":
            65
        }
    ]

    index_chunks(sample_chunks)

    results = semantic_search(
        query="How do I troubleshoot CrashLoopBackOff?",
        department="Engineering",
        source_document="kubernetes.pdf"
    )

    print(results)