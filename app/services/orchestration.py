"""
Query Orchestration Service - Engineer 5 (Orchestration)
Main pipeline orchestrator that connects:
  RRF Results → Hallucination Firewall → LLM → Response Formatter
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.models.schemas import QueryResponse, Citation
from app.services.grounding import HallucinationFirewall
from app.services.rrf_fusion import compute_rrf
from app.services.lexical_search import keyword_search


_client = None
_loaded_documents = None  # Cache for loaded PDF documents


def _load_real_documents() -> List[Dict[str, Any]]:
    """
    Load and chunk real documents from AWS.pdf and FAQs.pdf.
    Used as fallback when Engineer 1's database isn't ready.
    """
    global _loaded_documents
    if _loaded_documents is not None:
        return _loaded_documents

    chunks = []

    # Try to load PDFs using pymupdf
    try:
        import pymupdf
        base_path = Path(__file__).parent.parent.parent

        pdf_files = {
            "AWS.pdf": "AWS.pdf",
            "FAQs.pdf": "FAQs.pdf"
        }

        for doc_name, pdf_file in pdf_files.items():
            pdf_path = base_path / pdf_file
            if pdf_path.exists():
                try:
                    doc = pymupdf.open(pdf_path)
                    chunk_id_counter = 0
                    for page_num, page in enumerate(doc):
                        text = page.get_text()
                        # Split page into smaller chunks (roughly 500 chars each)
                        lines = text.split("\n")
                        current_chunk = ""
                        for line in lines:
                            current_chunk += line + "\n"
                            if len(current_chunk) > 500:
                                chunk_text = current_chunk.strip()
                                if chunk_text:
                                    chunks.append({
                                        "chunk_id": f"{doc_name.replace('.pdf', '')}_{page_num}_{chunk_id_counter}",
                                        "text_content": chunk_text[:1000],  # Max 1000 chars
                                        "metadata": {
                                            "source_document": doc_name,
                                            "page": page_num + 1,
                                            "section": "Content"
                                        }
                                    })
                                    chunk_id_counter += 1
                                current_chunk = ""

                        # Add remaining content
                        chunk_text = current_chunk.strip()
                        if chunk_text:
                            chunks.append({
                                "chunk_id": f"{doc_name.replace('.pdf', '')}_{page_num}_{chunk_id_counter}",
                                "text_content": chunk_text[:1000],
                                "metadata": {
                                    "source_document": doc_name,
                                    "page": page_num + 1,
                                    "section": "Content"
                                }
                            })
                    doc.close()
                    print(f"[ORCHESTRATION] Loaded {len([c for c in chunks if doc_name in c['metadata']['source_document']])} chunks from {doc_name}")
                except Exception as e:
                    print(f"[ORCHESTRATION] Failed to load {pdf_path}: {str(e)}")
    except ImportError:
        print("[ORCHESTRATION] pymupdf not available, using mock data")

    _loaded_documents = chunks if chunks else None
    return _loaded_documents


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

            # Step 3: Build context and call Gemini LLM
            context_blocks = []
            for chunk in top_chunks:
                block = f"<context_content source='{chunk.get('metadata', {}).get('source_document', 'Unknown')}'>\n{chunk.get('text_content', '')}\n</context_content>"
                context_blocks.append(block)

            joined_context = "\n\n".join(context_blocks)

            system_prompt = (
                "You are an elite Cloud Infrastructure Auditing Specialist. Answer the user query using ONLY the verified context text pieces provided below. "
                "If the answer cannot be confidently deduced from the context, respond with your exact fallback text pattern.\n\n"
                f"Context:\n{joined_context}\n\n"
                f"User Query: {user_query}"
            )

            try:
                print("[ORCHESTRATION] Calling Gemini LLM...")
                client = _get_client()
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=system_prompt
                )
                answer = response.text
                print(f"[ORCHESTRATION] Gemini response: {answer[:100]}...")
            except Exception as e:
                print(f"[ORCHESTRATION] LLM FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                return self._create_llm_error_response()

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

    def _simple_text_search(self, query: str, chunks: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Simple keyword matching on loaded PDF chunks.
        Returns chunks that contain query terms, ranked by match count.
        """
        if not chunks:
            return []

        query_terms = query.lower().split()
        scored_chunks = []

        for chunk in chunks:
            text = chunk.get("text_content", "").lower()
            # Count how many query terms appear in this chunk
            match_count = sum(1 for term in query_terms if term in text)
            if match_count > 0:
                scored_chunks.append((chunk, match_count))

        # Sort by match count descending, return top_n
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:top_n]]

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

        # If PostgreSQL unavailable, try simple text search on loaded PDFs
        if not sparse_results:
            loaded_docs = _load_real_documents()
            if loaded_docs:
                sparse_results = self._simple_text_search(query, loaded_docs, top_n=10)
                if sparse_results:
                    print(f"[ORCHESTRATION] Found {len(sparse_results)} results via simple text search")

        # Get dense results from Qdrant Vector Database (Engineer 2)
        dense_results = []
        try:
            from app.services.vector_search import semantic_search
            dense_results = semantic_search(query, limit=10)
        except ImportError:
            print(f"[ORCHESTRATION] Warning: Vector search dependencies not available, skipping dense search")
        except Exception as e:
            print(f"[ORCHESTRATION] Warning: Vector search failed ({str(e)}), using keyword search only")
            dense_results = []

        # Use Engineer 4's RRF to combine and rank results
        # If sparse_results empty (PostgreSQL unavailable), use dense results
        if not sparse_results:
            sparse_results = dense_results.copy() if dense_results else []

        # Fallback to mock data if both search methods return nothing
        if not dense_results and not sparse_results:
            print(f"[ORCHESTRATION] No real search results found, using mock data for testing")
            sparse_results = self._get_mock_fallback_data()

        results = compute_rrf(dense_results, sparse_results, k=3, top_n=3)


        # Convert Engineer 4's format to our expected format
        converted_results = []
        for result in results:
            converted = {
                "chunk_id": result.get("Chunk ID", result.get("chunk_id", "")),
                "text_content": result.get("text_content", ""),
                "metadata": {
                    "source_document": result.get("Source Document Name", result.get("source_document", "Unknown")),
                    "source": result.get("Source Document Name", result.get("source_document", "Unknown"))
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
                #fix
                chunk_id=str(chunk.get("chunk_id", "")),
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
            answer="Error: Unable to generate answer. Please check that GEMINI_API_KEY environment variable is set and Google Gemini API is accessible.",
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

    def _get_mock_fallback_data(self) -> List[Dict[str, Any]]:
        """
        Try to load real PDF content first, fall back to mock data if unavailable.
        """
        # Try real PDFs first
        real_chunks = _load_real_documents()
        if real_chunks and len(real_chunks) > 0:
            return real_chunks[:10]  # Return top 10 chunks

        # Fallback to mock data
        return [
            {
                "chunk_id": "faq_001_seven_rs",
                "text_content": "A critical first step is collecting application portfolio data evaluated against the seven common migration strategies (7 Rs): refactor, replatform, repurchase, rehost, relocate, retain, and retire.",
                "metadata": {
                    "source_document": "FAQs.pdf",
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
                "chunk_id": "aws_002_global_infrastructure",
                "text_content": "The AWS Cloud infrastructure is built around Regions and Availability Zones (AZs). The AWS Cloud operates 42 AZs within 16 geographic Regions around the world to maximize fault tolerance.",
                "metadata": {
                    "source_document": "AWS.pdf",
                    "section": "Global Infrastructure",
                    "page": 4
                }
            },
        ]


async def process_query(
    user_query: str,
    metadata_filter: Optional[str] = None,
    use_mock_rrf: bool = False
) -> QueryResponse:
    """
    Process a user query through the full RAG pipeline.

    Args:
        user_query: User's question
        metadata_filter: Optional metadata filter
        use_mock_rrf: Use mock RRF for testing (default: False)

    Returns:
        QueryResponse with answer and citations
    """
    orchestrator = QueryOrchestrator(use_mock_rrf=use_mock_rrf)
    return await orchestrator.orchestrate_query(user_query, metadata_filter)

