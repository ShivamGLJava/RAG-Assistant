from typing import List, Dict, Any
from langchain_text_splitters import CharacterTextSplitter


class FixedChunkingStrategy:
    """Fixed-size chunking with overlapping windows."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 52):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n"
        )

    def chunk(self, text: str, source_document: str, department: str) -> List[Dict[str, Any]]:
        """
        Split text into fixed-size chunks with metadata.

        Returns list of chunks with format:
        {
            "content": "chunk text",
            "source_document": "filename.pdf",
            "department": "Engineering",
            "chunk_id": 0
        }
        """
        chunks_text = self.splitter.split_text(text)

        chunks = []
        for chunk_id, chunk_text in enumerate(chunks_text):
            chunks.append({
                "content": chunk_text,
                "source_document": source_document,
                "department": department,
                "chunk_id": chunk_id,
                "chunk_size": len(chunk_text)
            })

        return chunks
