from fastapi import FastAPI, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, Citation
from app.services.hybrid_engine import HybridEngine
from app.services.generation import GenerationService
import random # Mock for vector generation

app = FastAPI(
    title="Enterprise RAG Assistant - Advanced Implementation",
    description="Engine-layer development focusing on Hybrid Search and Hallucination Guardrails.",
    version="1.1.0"
)

# Initialize Services
hybrid_engine = HybridEngine()
generation_service = GenerationService()

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "engine": "Advanced RAG", "version": "1.1.0"}

@app.post("/api/v1/chat", response_model=QueryResponse, tags=["RAG"])
async def chat_endpoint(request: QueryRequest):
    """
    Advanced RAG Orchestration:
    1. Query Parsing -> 2. Vectorization -> 3. Hybrid Search -> 4. Guarded Generation
    """
    try:
        # 1. Simulate Vectorization (Engineer 2's part)
        # In production: query_vector = embedding_model.encode(request.user_query)
        mock_vector = [random.uniform(-1, 1) for _ in range(384)]

        # 2. Execute Hybrid Search (Vector + Keyword)
        context_chunks = await hybrid_engine.hybrid_search(
            query=request.user_query,
            query_vector=mock_vector,
            dept_filter=request.metadata_filter
        )

        # 3. Guarded Generation (Hallucination Control)
        result = generation_service.generate_answer(
            query=request.user_query,
            context_chunks=context_chunks
        )

        return QueryResponse(
            answer=result["answer"],
            citations=[Citation(**c) for c in result["citations"]],
            status="trusted" if result["trusted"] else "fallback"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
