from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    user_query: str = Field(..., description="The natural language question from the user.")
    metadata_filter: Optional[str] = Field(None, description="Optional metadata tag to filter the search (e.g., 'Engineering').")

class Citation(BaseModel):
    document_name: str = Field(..., description="The name of the source document.")
    text_snippet: str = Field(..., description="The specific chunk of text retrieved from the document.")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from the RAG system.")
    citations: List[Citation] = Field(default_factory=list, description="A list of source citations used to generate the answer.")
    status: str = Field("success", description="The status of the query request.")
