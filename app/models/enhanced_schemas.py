"""
Enhanced Pydantic schemas for RAG search responses with evaluation metrics.
Implements confidence scoring, grounding validation, and performance metrics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# FACT VERIFICATION & GROUNDING EVIDENCE
# ============================================================================

class GroundingEvidence(BaseModel):
    """Evidence linking a fact to its source chunk."""
    fact: str = Field(..., description="The verified fact from the answer")
    source_chunk_id: str = Field(..., description="Chunk ID containing this fact")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")
    match_type: str = Field(default="exact", description="exact | semantic | partial")


class FactVerification(BaseModel):
    """Fact-checking results for hallucination prevention."""
    verified_facts: int = Field(default=0, description="Number of verified facts")
    unverified_facts: int = Field(default=0, description="Unverified but not contradicted")
    contradicted_facts: int = Field(default=0, description="Facts contradicting context")
    grounding_evidence: List[GroundingEvidence] = Field(
        default_factory=list, description="List of verified facts with sources"
    )
    verification_status: str = Field(
        default="complete", description="complete | partial | pending"
    )


# ============================================================================
# RETRIEVAL METRICS
# ============================================================================

class RetrievalMetrics(BaseModel):
    """Metrics for retrieval accuracy evaluation."""
    precision_at_3: float = Field(
        ..., ge=0.0, le=1.0, description="Precision@3 (relevance of top-3)"
    )
    mean_reciprocal_rank: float = Field(
        ..., ge=0.0, le=1.0, description="MRR score (position-weighted ranking)"
    )
    ndcg_score: float = Field(
        ..., ge=0.0, le=1.0, description="NDCG (discounted cumulative gain)"
    )
    keyword_coverage: float = Field(
        ..., ge=0.0, le=1.0, description="% of query terms covered in context"
    )
    matched_terms: List[str] = Field(
        default_factory=list, description="Tokens from query found in context"
    )
    coverage_status: str = Field(
        default="complete", description="complete | partial | low"
    )


# ============================================================================
# PROCESSING STAGES & PERFORMANCE
# ============================================================================

class ProcessingStage(BaseModel):
    """Individual stage latency breakdown."""
    stage_name: str = Field(..., description="Name of processing stage")
    duration_ms: float = Field(..., ge=0, description="Duration in milliseconds")
    status: str = Field(default="success", description="success | warning | error")


class ProcessingMetrics(BaseModel):
    """Detailed performance breakdown across execution stages."""
    total_duration_ms: float = Field(..., ge=0, description="Total response time")
    stages: List[ProcessingStage] = Field(
        default_factory=list, description="Per-stage timing breakdown"
    )
    bottleneck_stage: Optional[str] = Field(
        default=None, description="Slowest stage name"
    )
    optimization_potential: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Potential speedup (0-1)"
    )


# ============================================================================
# HALLUCINATION & GROUNDING METRICS
# ============================================================================

class HallucinationMetrics(BaseModel):
    """Metrics for detecting and quantifying hallucination risk."""
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in answer (0=unreliable, 1=certain)"
    )
    hallucination_risk: float = Field(
        ..., ge=0.0, le=1.0, description="Risk of fabrication (0=safe, 1=high risk)"
    )
    grounding_score: float = Field(
        ..., ge=0.0, le=1.0, description="Answer coverage by context (0=ungrounded, 1=fully)"
    )
    fact_verification: FactVerification = Field(
        ..., description="Detailed fact-checking results"
    )
    semantic_consistency: float = Field(
        ..., ge=0.0, le=1.0, description="Consistency between answer and context"
    )
    safety_verdict: str = Field(
        default="safe", description="safe | caution | unsafe"
    )


# ============================================================================
# CONTEXT CHUNK WITH METRICS
# ============================================================================

class ContextChunk(BaseModel):
    """Context chunk with extended metadata."""
    rank: int = Field(..., description="Rank in fusion results (1-indexed)")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    rrf_score: float = Field(..., ge=0.0, le=1.0, description="RRF fusion score")
    source_document: str = Field(..., description="Source document name")
    text_content: str = Field(..., description="Chunk text content")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Semantic relevance to query"
    )
    grounding_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="% of answer sourced from this chunk"
    )
    coverage_tokens: List[str] = Field(
        default_factory=list, description="Query tokens found in this chunk"
    )


# ============================================================================
# SEARCH REQUEST & RESPONSE
# ============================================================================

class SearchRequest(BaseModel):
    """Request schema for hybrid search endpoint."""
    user_query: str = Field(..., min_length=1, description="User's search query")
    include_metrics: bool = Field(
        default=True, description="Include detailed metrics in response"
    )
    include_logs: bool = Field(
        default=True, description="Include execution logs in response"
    )


class SearchResponse(BaseModel):
    """Enhanced search response with full evaluation metrics."""

    # Core response
    answer: str = Field(..., description="Generated answer from LLM")
    context_chunks: List[ContextChunk] = Field(
        ..., description="Retrieved context chunks"
    )

    # Tracking
    request_id: str = Field(..., description="Unique request identifier (UUID)")
    timestamp: datetime = Field(..., description="Response timestamp (ISO 8601)")

    # Performance metrics
    processing_metrics: ProcessingMetrics = Field(
        ..., description="Detailed performance breakdown"
    )

    # Retrieval metrics
    retrieval_metrics: RetrievalMetrics = Field(
        ..., description="Retrieval accuracy metrics"
    )

    # Hallucination prevention
    hallucination_metrics: HallucinationMetrics = Field(
        ..., description="Hallucination risk and grounding metrics"
    )

    # Quality signals
    overall_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Combined quality score (0-1)"
    )
    quality_grade: str = Field(
        default="B", description="Grade: A+ | A | B | C | D (for display)"
    )

    # Optional execution logs
    execution_logs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Structured execution logs (if requested)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The 7 Rs are: Rehost, Replatform...",
                "context_chunks": [
                    {
                        "rank": 1,
                        "chunk_id": "faq_001",
                        "rrf_score": 0.0327,
                        "source_document": "FAQs.pdf",
                        "text_content": "...",
                        "relevance_score": 0.95,
                        "grounding_contribution": 0.85,
                        "coverage_tokens": ["7", "rs", "migration"]
                    }
                ],
                "request_id": "req_550e8400-e29b-41d4-a716-446655440000",
                "overall_quality_score": 0.92,
                "quality_grade": "A"
            }
        }
