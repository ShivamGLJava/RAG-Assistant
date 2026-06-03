import fitz  # PyMuPDF
from typing import List, Dict, Any


class DocumentLoader:
    """Extract text from PDF documents using PyMuPDF."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = fitz.open(file_path)

    def extract_text(self) -> str:
        """Extract all text from PDF."""
        text = ""
        for page_num in range(len(self.document)):
            page = self.document[page_num]
            text += page.get_text()
        return text

    def extract_pages(self) -> List[Dict[str, Any]]:
        """Extract text per page with metadata."""
        pages = []
        for page_num in range(len(self.document)):
            page = self.document[page_num]
            pages.append({
                "page_num": page_num + 1,
                "text": page.get_text(),
                "metadata": {
                    "source": self.file_path,
                    "page": page_num + 1
                }
            })
        return pages

    def close(self):
        """Close the document."""
        self.document.close()
