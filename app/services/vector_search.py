from qdrant_client.models import PointStruct

from embedding_model import generate_embedding
from qdrant_store import (
    client,
    COLLECTION_NAME,
    initialize_collection
)
initialize_collection()

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
    limit: int = 10
):

    query_vector = generate_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    output = []

    for point in results.points:

        output.append(
            {
                "score": point.score,
                "content": point.payload["content"],
                "source_document": point.payload["source_document"],
                "department": point.payload["department"],
                "chunk_id": point.payload["chunk_id"],
                "chunk_size": point.payload["chunk_size"]
            }
        )

    return output


if __name__ == "__main__":

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
        "How do I troubleshoot CrashLoopBackOff?"
    )

    print(results)