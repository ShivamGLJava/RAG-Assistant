import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from app.services.lexical_search import keyword_search
from app.services.rrf_fusion import compute_rrf
from app.services.grounding import HallucinationFirewall
from app.services.orchestration import process_query

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

_client = None

DOCUMENTS = {
    "aws": "AWS.pdf",
    "qna": "QnA.pdf"
}


def _get_client():
    """Lazy-load Gemini client only when needed."""
    global _client
    if _client is None:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set or is empty")
        _client = genai.Client(api_key=api_key)
    return _client


class QueryRequest(BaseModel):
    user_query: str


class ContextChunk(BaseModel):
    rank: int
    chunk_id: str
    rrf_score: float
    source_document: str
    text_content: str


class TimingInfo(BaseModel):
    stage: str
    duration_ms: float


class TelemetryInfo(BaseModel):
    total_duration_ms: float
    timings: List[TimingInfo]
    bottleneck_stage: str
    firewall_confidence_score: float


class QueryResponse(BaseModel):
    answer: str
    context_chunks: List[ContextChunk]
    telemetry: Optional[TelemetryInfo] = None


app = FastAPI(
    title="Cloud Infrastructure Auditing Engine",
    description="Production-ready hybrid lexical-dense retrieval with RRF fusion for cloud infrastructure best practices",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)


@app.middleware("http")
async def cors_middleware(request, call_next):
    """Manually add CORS headers to all responses."""
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600",
            },
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response


async def _fetch_vector_search_results(query: str) -> list:
    """
    Fetch dense vector search results from cloud infrastructure context.
    Grounded by text blocks extracted from AWS.pdf and QnA.pdf.
    """
    return [
        {
            "chunk_id": "faq_001_seven_rs",
            "text_content": "A critical first step is collecting application portfolio data evaluated against the seven common migration strategies (7 Rs): refactor, replatform, repurchase, rehost, relocate, retain, and retire.",
            "metadata": {
                "source_document": "QnA.pdf",
                "section": "Migration Strategies",
                "page": 6
            }
        },
        {
            "chunk_id": "aws_001_iaas_paas_saas",
            "text_content": "Understanding the differences between Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS) provides different levels of control, flexibility, and management.",
            "metadata": {
                "source_document": "AWS.pdf",
                "section": "Cloud Computing Models",
                "page": 2
            }
        },
        {
            "chunk_id": "faq_002_discovery_rules",
            "text_content": "When assessing if an application can be retired, you must confirm that workloads aren't dependent on it. Use discovery tooling to show connections initiated to a server scheduled for retirement.",
            "metadata": {
                "source_document": "QnA.pdf",
                "section": "Network Auditing",
                "page": 6
            }
        },
        {
            "chunk_id": "aws_002_global_infrastructure",
            "text_content": "The AWS Cloud infrastructure is built around Regions and Availability Zones (AZs). The AWS Cloud operates 42 AZs within 16 geographic Regions around the world to maximize fault tolerance.",
            "metadata": {
                "source_document": "AWS.pdf",
                "section": "Global Infrastructure",
                "page": 4
            }
        },
        {
            "chunk_id": "faq_003_controlled_stops",
            "text_content": "In your migration plan, schedule time for a controlled stop. A controlled stop pauses the migration process to identify the potential for disruption if an application is retired by simulating the retirement.",
            "metadata": {
                "source_document": "QnA.pdf",
                "section": "Application Lifecycle",
                "page": 8
            }
        }
    ]


@app.get("/health", tags=["System"])
async def health_check():
    """Service liveness probe."""
    return {"status": "healthy"}


@app.get("/api/v1/status", tags=["System"])
async def pipeline_status():
    """Returns the current status of RAG pipeline components and configured data sources."""
    return {
        "status": "operational",
        "engineer_1_ingestion": "integrated",
        "engineer_2_qdrant": "placeholder_ready",
        "engineer_3_fastapi": "ready",
        "engineer_4_hybrid_search": "production",
        "data_sources": DOCUMENTS,
        "retrieval_strategy": "hybrid_lexical_dense_rrf",
        "rrf_config": {
            "smoothing_constant": 60,
            "top_n_candidates": 3
        }
    }


@app.options("/api/v1/search")
async def options_search():
    """Handle CORS preflight requests."""
    return {}


@app.post("/api/v1/search", tags=["RAG"])
async def search(request: QueryRequest):
    """
    Core hybrid retrieval and answer generation orchestration.
    Integrates parallel lexical and dense retrieval tracks with RRF fusion.
    Applies hallucination firewall before calling LLM.
    """
    # Use the QueryOrchestrator to handle the full pipeline
    response = await process_query(request.user_query)

    # Convert Citation objects to ContextChunk for response
    context_chunks = []
    if response.citations:
        for rank, citation in enumerate(response.citations, start=1):
            context_chunks.append(
                ContextChunk(
                    rank=rank,
                    chunk_id=citation.chunk_id,
                    rrf_score=citation.relevance_score,
                    source_document=citation.document_name,
                    text_content=citation.text_snippet
                )
            )

    # Convert telemetry if present
    telemetry_info = None
    if response.telemetry:
        telemetry_info = TelemetryInfo(
            total_duration_ms=response.telemetry.total_duration_ms,
            timings=[TimingInfo(stage=t.stage, duration_ms=t.duration_ms) for t in response.telemetry.timings],
            bottleneck_stage=response.telemetry.bottleneck_stage,
            firewall_confidence_score=response.telemetry.firewall_confidence_score
        )

    result = QueryResponse(answer=response.answer, context_chunks=context_chunks, telemetry=telemetry_info)
    # Return as dict to ensure FastAPI includes all fields including optional telemetry
    return result.model_dump(exclude_none=False)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
