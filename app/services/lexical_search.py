import os
import json
import psycopg2
from psycopg2 import pool

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "rag_assistant")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

_connection_pool = None

try:
    _connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )
except Exception:
    _connection_pool = None


def keyword_search(query: str, top_n: int = 20) -> list:
    """
    Execute PostgreSQL Full-Text Search on technical_chunks table.
    Returns list of dictionaries with chunk_id, text_content, and metadata.
    Falls back to empty list if database is unavailable.
    """
    if not _connection_pool:
        return []

    try:
        connection = _connection_pool.getconn()
        cursor = connection.cursor()

        sql = """
        SELECT
            chunk_id,
            text_content,
            COALESCE(metadata, '{}'::jsonb) as metadata
        FROM technical_chunks
        WHERE text_tsv @@ plainto_tsquery('english', %s)
        ORDER BY
            ts_rank(text_tsv, plainto_tsquery('english', %s)) DESC
        LIMIT %s;
        """

        cursor.execute(sql, (query, query, top_n))
        rows = cursor.fetchall()
        cursor.close()
        _connection_pool.putconn(connection)

        results = []
        for row in rows:
            chunk_id, text_content, metadata_obj = row

            if isinstance(metadata_obj, dict):
                metadata_dict = metadata_obj
            elif isinstance(metadata_obj, str):
                try:
                    metadata_dict = json.loads(metadata_obj)
                except json.JSONDecodeError:
                    metadata_dict = {}
            else:
                metadata_dict = {}

            results.append({
                "chunk_id": chunk_id,
                "text_content": text_content,
                "metadata": metadata_dict
            })

        return results

    except Exception as e:
        return []
