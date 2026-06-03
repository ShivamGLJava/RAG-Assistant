from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import VectorParams

COLLECTION_NAME = "enterprise_docs"

client = QdrantClient(
    path="./qdrant_data"
)

import atexit

atexit.register(client.close)


def initialize_collection():

    collections = client.get_collections()

    existing_collections = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME not in existing_collections:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

        print(f"Collection '{COLLECTION_NAME}' created.")

    else:

        print(f"Collection '{COLLECTION_NAME}' already exists.")


if __name__ == "__main__":

    initialize_collection()