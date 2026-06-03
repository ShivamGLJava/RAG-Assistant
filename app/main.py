from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from app.services.lexical_search import keyword_search
from app.services.rrf_fusion import compute_rrf
from app.models.schemas import QueryRequest as ChatQueryRequest, QueryResponse as ChatQueryResponse

class QueryRequest(BaseModel):
    user_query: str

class ContextChunk(BaseModel):
    rank: int
    chunk_id: str
    rrf_score: float
    source_document: str
    text_content: str

class QueryResponse(BaseModel):
    answer: str
    context_chunks: List[ContextChunk]

app = FastAPI(title="RAG-Assistant", version="1.0.0")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/search", response_model=QueryResponse)
async def search(request: QueryRequest):
    """Engineer 4's RRF + Hybrid Search Endpoint"""
    dense_mock_results = [
        {
            "chunk_id": "doc_002_chk_3",
            "text_content": "Container CrashLoopBackOff occurs when your pod fails to start. Check logs with kubectl logs.",
            "metadata": {"source_document": "kubernetes_handbook.md", "source": "kubernetes_handbook.md"}
        },
        {
            "chunk_id": "doc_004_chk_1",
            "text_content": "Kubernetes debugging: inspect pod status and resource limits to resolve CrashLoopBackOff.",
            "metadata": {"source_document": "k8s_debugging.md", "source": "k8s_debugging.md"}
        },
        {
            "chunk_id": "doc_001_chk_1",
            "text_content": "To fix a 502 Bad Gateway error, check your upstream server status and verify network connectivity.",
            "metadata": {"source_document": "troubleshooting_guide.md", "source": "troubleshooting_guide.md"}
        }
    ]

    sparse_results = keyword_search(request.user_query)
    # If sparse_results empty (PostgreSQL unavailable), use mock sparse results
    if not sparse_results:
        sparse_results = dense_mock_results.copy()
    fused_results = compute_rrf(dense_mock_results, sparse_results, k=10, top_n=3)

    context_chunks = []
    for rank, result in enumerate(fused_results, start=1):
        c_id = str(result.get("chunk_id", result.get("Chunk ID", "N/A")))
        score = float(result.get("rrf_score", result.get("Calculated RRF Score", 0.0)))
        meta = result.get("metadata", {})
        doc_name = meta.get("source_document", meta.get("source", result.get("source_document", "Unknown")))
        text = result.get("text_content", "")

        context_chunks.append(
            ContextChunk(
                rank=rank,
                chunk_id=c_id,
                rrf_score=score,
                source_document=doc_name,
                text_content=text
            )
        )

    answer = f"Retrieved {len(context_chunks)} relevant context chunks for: {request.user_query}"
    return QueryResponse(answer=answer, context_chunks=context_chunks)


@app.post("/api/v1/chat", response_model=ChatQueryResponse, tags=["RAG"])
async def chat_endpoint(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    Main RAG chat endpoint - Engineer 5 (Orchestration) implementation.
    Uses Engineer 4's RRF results with hallucination firewall and LLM.

    Input: QueryRequest with user_query and optional metadata_filter
    Output: QueryResponse with answer, citations, confidence_score, and status

    Pipeline:
    1. Accept user query
    2. Retrieve relevant chunks via RRF (hybrid search)
    3. Apply hallucination firewall (confidence check)
    4. If allowed, call Ollama LLM with context
    5. Format response with source citations
    6. Return grounded answer

    Status values:
    - "success": Answer generated successfully
    - "no_reliable_answer": Firewall blocked (insufficient confidence)
    - "error": System error occurred
    """
    from app.services.orchestration import process_query

    try:
        response = await process_query(
            user_query=request.user_query,
            metadata_filter=request.metadata_filter,
            use_mock_rrf=False  # Now using real RRF from Engineer 4
        )
        return response
    except Exception as e:
        return ChatQueryResponse(
            answer=f"Error processing query: {str(e)}",
            citations=[],
            status="error",
            confidence_score=0.0
        )
