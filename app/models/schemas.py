from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    user_query: str = Field(..., description="The natural language question from the user.")
    metadata_filter: Optional[str] = Field(None, description="Optional metadata tag to filter the search (e.g., 'Engineering').")

class Citation(BaseModel):
    document_name: str = Field(..., description="The name of the source document.")
    text_snippet: str = Field(..., description="The specific chunk of text retrieved from the document.")
    chunk_id: str = Field(..., description="Unique identifier for the chunk.")
    relevance_score: float = Field(..., description="Relevance score from hybrid search (0-1).")

class TimingData(BaseModel):
    stage: str = Field(..., description="Pipeline stage name (retrieval, ranking, firewall, llm, formatting).")
    duration_ms: float = Field(..., description="Duration of this stage in milliseconds.")

class TelemetryData(BaseModel):
    total_duration_ms: float = Field(..., description="Total time from query start to response end.")
    timings: List[TimingData] = Field(default_factory=list, description="Per-stage timing breakdown.")
    bottleneck_stage: str = Field(..., description="The slowest stage in the pipeline.")
    firewall_confidence_score: float = Field(..., description="Confidence score from hallucination firewall (0-1).")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from the RAG system.")
    citations: List[Citation] = Field(default_factory=list, description="A list of source citations used to generate the answer.")
    status: str = Field("success", description="The status of the query request (success, no_reliable_answer, error).")
    confidence_score: Optional[float] = Field(None, description="Overall confidence score of the retrieval (0-1).")
    telemetry: Optional[TelemetryData] = Field(None, description="Telemetry data including pipeline stage timings.")
