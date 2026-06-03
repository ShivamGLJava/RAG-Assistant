"""
Query Orchestration Service - Engineer 5 (Orchestration)
Main pipeline orchestrator that connects:
  RRF Results → Hallucination Firewall → LLM → Response Formatter
"""

from typing import List, Dict, Any, Optional
from app.models.schemas import QueryResponse, Citation
from app.services.grounding import HallucinationFirewall
from app.services.hf_llm_integration import HuggingFaceLLM
from app.services.rrf_fusion import compute_rrf
from app.services.lexical_search import keyword_search


class QueryOrchestrator:
    """
    Main orchestration service that coordinates the entire RAG pipeline.
    Connects search results → firewall → LLM → formatted response.
    """

    def __init__(self, use_mock_rrf: bool = True):
        """
        Initialize orchestrator.

        Args:
            use_mock_rrf: Use mock RRF (True) or real RRF when ready (False)
        """
        self.use_mock_rrf = use_mock_rrf
        self.firewall = HallucinationFirewall()

    async def orchestrate_query(
        self,
        user_query: str,
        metadata_filter: Optional[str] = None
    ) -> QueryResponse:
        """
        Main orchestration pipeline for a user query.

        Flow:
        1. Retrieve relevant chunks via RRF (mock or real)
        2. Apply hallucination firewall (check confidence)
        3. If allowed, call LLM with context
        4. Format response with citations
        5. Return to user

        Args:
            user_query: User's question
            metadata_filter: Optional metadata filter (e.g., "Engineering")

        Returns:
            QueryResponse with answer, citations, and status
        """
        try:
            # Step 1: Get RRF results (mock or real)
            print(f"\n[ORCHESTRATION] Processing query: {user_query[:50]}...")
            rrf_results = self._get_search_results(user_query, metadata_filter)

            if not rrf_results:
                print("[ORCHESTRATION] No search results found")
                return self._create_no_results_response(user_query)

            print(f"[ORCHESTRATION] Retrieved {len(rrf_results)} chunks")

            # Step 2: Apply hallucination firewall
            can_answer, top_chunks = self.firewall.should_call_llm(rrf_results)

            if not can_answer:
                print("[ORCHESTRATION] Hallucination firewall BLOCKED answer (low confidence)")
                return self._create_firewall_blocked_response(rrf_results[0] if rrf_results else None)

            top_score = rrf_results[0].get("rrf_score", 0.0)
            print(f"[ORCHESTRATION] Hallucination firewall ALLOWED answer (score: {top_score:.2f})")

            # Step 3: Build context and call Hugging Face LLM
            context = HuggingFaceLLM.build_context(top_chunks)
            answer = HuggingFaceLLM.query(user_query, context)

            if not answer:
                print("[ORCHESTRATION] LLM failed to generate answer")
                return self._create_llm_error_response()

            print("[ORCHESTRATION] LLM generated answer successfully")

            # Step 4: Format response with citations
            citations = self._format_citations(top_chunks)
            response = QueryResponse(
                answer=answer,
                citations=citations,
                status="success",
                confidence_score=top_score
            )

            print("[ORCHESTRATION] Query completed successfully")
            return response

        except Exception as e:
            print(f"[ERROR] Orchestration failed: {str(e)}")
            return self._create_error_response(str(e))

    def _get_search_results(
        self,
        query: str,
        metadata_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get search results from RRF (Engineer 4's real implementation).

        Args:
            query: Search query
            metadata_filter: Optional department filter

        Returns:
            List of ranked results with scores
        """
        # Get sparse results from PostgreSQL Full-Text Search (Engineer 4)
        sparse_results = keyword_search(query, top_n=10)

        # TODO: Get dense results from Qdrant (Engineer 2)
        # For now, using mock dense results
        dense_results = [
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

        # Use Engineer 4's RRF to combine and rank results
        # If sparse_results empty (PostgreSQL unavailable), use mock sparse results
        if not sparse_results:
            sparse_results = dense_results.copy()
        results = compute_rrf(dense_results, sparse_results, k=10, top_n=10)

        # Convert Engineer 4's format to our expected format
        converted_results = []
        for result in results:
            converted = {
                "chunk_id": result.get("Chunk ID", result.get("chunk_id", "")),
                "text_content": result.get("text_content", ""),
                "metadata": {
                    "source_document": result.get("Source Document Name", "Unknown"),
                    "source": result.get("Source Document Name", "Unknown")
                },
                "rrf_score": result.get("Calculated RRF Score", result.get("rrf_score", 0.0))
            }
            converted_results.append(converted)

        # Filter by department if specified
        if metadata_filter:
            converted_results = HallucinationFirewall.filter_by_department(converted_results, metadata_filter)

        return converted_results

    def _format_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """
        Convert chunks to Citation objects for response.

        Args:
            chunks: List of retrieved chunks

        Returns:
            List of Citation objects
        """
        citations = []

        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            citation = Citation(
                document_name=metadata.get("source_document", "Unknown"),
                text_snippet=chunk.get("text_content", "")[:200],  # First 200 chars
                chunk_id=chunk.get("chunk_id", ""),
                relevance_score=chunk.get("rrf_score", 0.0)
            )
            citations.append(citation)

        return citations

    def _create_no_results_response(self, query: str) -> QueryResponse:
        """Create response when no search results found."""
        return QueryResponse(
            answer="No documents found matching your query. Please try a different search term.",
            citations=[],
            status="no_reliable_answer",
            confidence_score=0.0
        )

    def _create_firewall_blocked_response(
        self,
        top_result: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
        """Create response when firewall blocks answer."""
        fallback = HallucinationFirewall.get_fallback_response("")
        return QueryResponse(
            answer=fallback["answer"],
            citations=[],
            status="no_reliable_answer",
            confidence_score=0.0
        )

    def _create_llm_error_response(self) -> QueryResponse:
        """Create response when LLM fails."""
        return QueryResponse(
            answer="Error: Unable to generate answer. Please check that HF_API_TOKEN environment variable is set and Hugging Face API is accessible.",
            citations=[],
            status="error",
            confidence_score=0.0
        )

    def _create_error_response(self, error_msg: str) -> QueryResponse:
        """Create response for general errors."""
        return QueryResponse(
            answer=f"Error processing your query: {error_msg}",
            citations=[],
            status="error",
            confidence_score=0.0
        )


# Convenience function for endpoint
async def process_query(
    user_query: str,
    metadata_filter: Optional[str] = None,
    use_mock_rrf: bool = True
) -> QueryResponse:
    """
    Process a user query through the full RAG pipeline.

    Args:
        user_query: User's question
        metadata_filter: Optional metadata filter
        use_mock_rrf: Use mock RRF for testing

    Returns:
        QueryResponse with answer and citations
    """
    orchestrator = QueryOrchestrator(use_mock_rrf=use_mock_rrf)
    return await orchestrator.orchestrate_query(user_query, metadata_filter)
