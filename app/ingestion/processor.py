import fitz  # PyMuPDF
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

class DocumentProcessor:
    def __init__(self):
        # Recursive splitter: Splits at double newline, then single, then space
        self.fixed_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=51,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF or Text/Markdown and returns a list of page-level data.
        """
        # Handle non-PDF files (Markdown, Text)
        if not file_path.lower().endswith('.pdf'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return [{
                "text": text,
                "metadata": {
                    "source": file_path.split("/")[-1],
                    "page": 1
                }
            }]

        # Handle PDF files
        doc = fitz.open(file_path)
        pages = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            pages.append({
                "text": text,
                "metadata": {
                    "source": file_path.split("/")[-1],
                    "page": page_num + 1
                }
            })
        return pages

    def create_chunks(self, pages: List[Dict[str, Any]], department: str) -> List[Dict[str, Any]]:
        """
        Processes pages and creates chunks with enriched metadata.
        """
        final_chunks = []
        for page in pages:
            # We use the fixed splitter for baseline accuracy
            chunks = self.fixed_splitter.split_text(page["text"])
            
            for i, chunk_text in enumerate(chunks):
                final_chunks.append({
                    "id": str(uuid.uuid4()),
                    "content": chunk_text,
                    "metadata": {
                        **page["metadata"],
                        "department": department,
                        "chunk_index": i,
                        "chunk_type": "fixed"
                    }
                })
        return final_chunks

    # TODO: Implement Semantic Chunking (Bonus Innovation)
    # This involves comparing sentence embeddings to find topical breaks.
