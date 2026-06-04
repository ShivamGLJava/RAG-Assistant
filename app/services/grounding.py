"""
Hallucination Control Firewall - Engineer 5 (Orchestration)
Prevents LLM from generating unsupported answers.
Critical safety mechanism for production RAG systems.
"""

from typing import List, Dict, Any, Tuple, Optional


class HallucinationFirewall:
    """
    Controls when to call the LLM vs return fallback message.
    This is the key component that prevents hallucinations by ensuring
    the LLM only generates answers from retrieved context.
    """

    # Confidence threshold below which we don't call LLM (adjusted for k=60 RRF scoring)
    CONFIDENCE_THRESHOLD = 0.01

    # Fallback message when firewall blocks answer
    FALLBACK_ANSWER = (
        "I cannot find sufficient information in the knowledge base to answer this question reliably. "
        "Please try rephrasing your query or consult the documentation directly."
    )

    @staticmethod
    def should_call_llm(
        rrf_results: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """
        Determines if retrieval results have sufficient confidence to call LLM.

        This is the core hallucination prevention mechanism:
        - If top result score >= CONFIDENCE_THRESHOLD: Allow LLM to generate
        - If top result score < CONFIDENCE_THRESHOLD: Block LLM, return fallback
        - If no results: Block LLM, return fallback

        Args:
            rrf_results: List of chunks from RRF with scores (0-1)

        Returns:
            Tuple of (should_call_llm: bool, top_chunks: List or None)
            - (True, [chunk1, chunk2, chunk3]) if safe to call LLM
            - (False, None) if should return fallback
        """
        # No results at all - definitely return fallback
        if not rrf_results or len(rrf_results) == 0:
            return False, None

        # Check top result's confidence score
        top_result = rrf_results[0]
        top_score = top_result.get("rrf_score", 0.0)

        # Score too low - return fallback to prevent hallucination
        if top_score < HallucinationFirewall.CONFIDENCE_THRESHOLD:
            return False, None

        # Confidence sufficient - return top 3 chunks for LLM context
        top_chunks = rrf_results[:3]
        return True, top_chunks

    @staticmethod
    def get_fallback_response(query: str) -> Dict[str, Any]:
        """
        Returns fallback response structure when firewall blocks answer.

        Args:
            query: Original user query (for logging/reference)

        Returns:
            Dict with answer, empty citations, error status
        """
        return {
            "answer": HallucinationFirewall.FALLBACK_ANSWER,
            "citations": [],
            "status": "no_reliable_answer",
            "confidence_score": 0.0
        }

    @staticmethod
    def get_confidence_label(score: float) -> str:
        """
        Human-readable confidence level description.

        Args:
            score: Confidence score 0-1

        Returns:
            Descriptive label for confidence level
        """
        if score < 0.1:
            return "Very Low Confidence"
        elif score < 0.3:
            return "Low Confidence"
        elif score < 0.6:
            return "Medium Confidence"
        elif score < 0.85:
            return "High Confidence"
        else:
            return "Very High Confidence"

    @staticmethod
    def validate_rrf_results(rrf_results: List[Dict[str, Any]]) -> bool:
        """
        Validates that RRF results have required fields.

        Args:
            rrf_results: List of chunks from RRF

        Returns:
            True if valid, False if missing required fields
        """
        required_fields = ["chunk_id", "text_content", "metadata", "rrf_score"]

        for result in rrf_results:
            for field in required_fields:
                if field not in result:
                    return False
            # Check metadata has required fields
            if "source_document" not in result.get("metadata", {}):
                return False

        return True

    @staticmethod
    def filter_by_department(
        rrf_results: List[Dict[str, Any]],
        department: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Filters RRF results by department metadata if specified.

        Args:
            rrf_results: List of chunks from RRF
            department: Department filter (e.g., "Engineering")

        Returns:
            Filtered list of results, or original if no filter specified
        """
        if not department:
            return rrf_results

        filtered = [
            r for r in rrf_results
            if r.get("metadata", {}).get("department", "").lower() == department.lower()
        ]

        return filtered if filtered else rrf_results

    @staticmethod
    def log_firewall_decision(
        query: str,
        top_score: float,
        decision: bool,
        reason: str = ""
    ) -> None:
        """
        Logs firewall decision for monitoring and debugging.

        Args:
            query: User query
            top_score: Top RRF score
            decision: Whether LLM was called
            reason: Reason for decision
        """
        action = "ALLOW" if decision else "BLOCK"
        confidence = HallucinationFirewall.get_confidence_label(top_score)

        print(f"[FIREWALL] {action} | Score: {top_score:.2f} ({confidence}) | Query: {query[:50]}...")
        if reason:
            print(f"[FIREWALL] Reason: {reason}")
