from pathlib import Path
import atexit

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams
)

from app.services.qdrant_lock_manager import (
    cleanup_stale_locks
)

COLLECTION_NAME = "enterprise_docs"

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Local Qdrant storage path
QDRANT_PATH = BASE_DIR / "qdrant_data"


def get_qdrant_client():
    """
    Create a Qdrant client after removing
    any stale lock files.
    """

    cleanup_stale_locks()

    return QdrantClient(
        path=str(QDRANT_PATH)
    )


# Initialize client
client = get_qdrant_client()

# Ensure proper shutdown
atexit.register(client.close)


def initialize_collection():
    """
    Create collection if it does not exist.
    """

    collections = client.get_collections()

    existing_collections = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME not in existing_collections:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )

        print(
            f"Collection '{COLLECTION_NAME}' created."
        )

    else:

        print(
            f"Collection '{COLLECTION_NAME}' already exists."
        )


def delete_collection():
    """
    Delete collection if needed.
    Useful during development/testing.
    """

    collections = client.get_collections()

    existing_collections = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME in existing_collections:

        client.delete_collection(
            collection_name=COLLECTION_NAME
        )

        print(
            f"Collection '{COLLECTION_NAME}' deleted."
        )


if __name__ == "__main__":

    initialize_collection()