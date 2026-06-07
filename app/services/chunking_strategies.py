from typing import List, Dict, Any
import numpy as np
from langchain_text_splitters import CharacterTextSplitter
import nltk
from nltk.tokenize import sent_tokenize
from app.services.embedding_model import generate_embedding

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


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
            "chunk_id": 0,
            "strategy": "fixed"
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
                "chunk_size": len(chunk_text),
                "strategy": "fixed"
            })

        return chunks


class SemanticChunkingStrategy:
    """Semantic chunking based on sentence similarity using HF Inference API."""

    def __init__(self, similarity_threshold: float = 0.55, max_chunk_size: int = 512):
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        print("   • Using HF Inference API for embeddings (all-roberta-large-v1)...")

    def chunk(self, text: str, source_document: str, department: str) -> List[Dict[str, Any]]:
        """
        Split text into semantically coherent chunks.

        Process:
        1. Split text into sentences
        2. Get embeddings for each sentence
        3. Calculate cosine similarity between consecutive sentences
        4. Merge sentences with high similarity (> threshold)
        5. Create chunks from merged sentences

        Returns list of chunks with metadata.
        """
        sentences = sent_tokenize(text)

        if len(sentences) == 0:
            return []

        if len(sentences) == 1:
            return [{
                "content": sentences[0],
                "source_document": source_document,
                "department": department,
                "chunk_id": 0,
                "chunk_size": len(sentences[0]),
                "strategy": "semantic"
            }]

        # Get embeddings for all sentences via HF API
        print(f"   • Embedding {len(sentences)} sentences via HF Inference API...")
        embeddings = []
        for sentence in sentences:
            embedding = generate_embedding(sentence)
            embeddings.append(embedding)
        embeddings = np.array(embeddings)

        # Calculate similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # Improved grouping: combine similarity and chunk size constraints
        groups = []
        current_group = [sentences[0]]
        current_size = len(sentences[0])

        for i, similarity in enumerate(similarities):
            next_sentence = sentences[i + 1]
            next_size = len(next_sentence)
            potential_size = current_size + len(" ") + next_size

            # Keep adding sentences if:
            # 1. Similarity is high AND
            # 2. Adding won't exceed max_chunk_size
            # This ensures semantic coherence while respecting size constraints
            if similarity > self.similarity_threshold and potential_size <= self.max_chunk_size:
                current_group.append(next_sentence)
                current_size = potential_size
            else:
                # Start new group if similarity is low OR size would be exceeded
                if current_group:
                    groups.append(" ".join(current_group))
                current_group = [next_sentence]
                current_size = next_size

        # Add last group
        if current_group:
            groups.append(" ".join(current_group))

        # Create chunks from groups
        chunks = []
        for chunk_id, group in enumerate(groups):
            chunks.append({
                "content": group,
                "source_document": source_document,
                "department": department,
                "chunk_id": chunk_id,
                "chunk_size": len(group),
                "strategy": "semantic"
            })

        return chunks

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
