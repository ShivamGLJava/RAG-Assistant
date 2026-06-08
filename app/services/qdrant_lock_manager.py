from pathlib import Path


LOCK_PATHS = [
    Path("qdrant_data/.lock"),
    Path("app/services/qdrant_data/.lock")
]


def cleanup_stale_locks():
    """
    Remove stale lock files before Qdrant startup.
    """

    for lock_path in LOCK_PATHS:

        if lock_path.exists():

            try:
                lock_path.unlink()

                print(
                    f"Removed stale lock: {lock_path}"
                )

            except Exception as e:

                print(
                    f"Could not remove {lock_path}: {e}"
                )