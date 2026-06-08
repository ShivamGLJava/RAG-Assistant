"""
Metrics calculation utilities for RAG evaluation.
Implements precision, MRR, NDCG, coverage, and hallucination risk scoring.
"""

import re
from typing import List, Set, Tuple
from collections import Counter


class RetrievalMetricsCalculator:
    """Calculate retrieval quality metrics."""

    @staticmethod
    def tokenize(text: str) -> Set[str]:
        """Tokenize text into lowercase alphanumeric tokens."""
        tokens = re.findall(r'\w+', text.lower())
        return set(tokens)

    @staticmethod
    def calculate_keyword_coverage(query: str, context_text: str) -> Tuple[float, List[str]]:
        """
        Calculate what percentage of query tokens appear in context.

        Returns:
            (coverage_score: 0-1, matched_tokens: List[str])
        """
        query_tokens = RetrievalMetricsCalculator.tokenize(query)
        context_tokens = RetrievalMetricsCalculator.tokenize(context_text)

        if not query_tokens:
            return 0.0, []

        matched = query_tokens.intersection(context_tokens)
        coverage = len(matched) / len(query_tokens)

        return coverage, list(matched)

    @staticmethod
    def calculate_precision_at_k(
        relevant_chunks: List[int], k: int = 3
    ) -> float:
        """
        Calculate Precision@K.

        Args:
            relevant_chunks: List of 1s (relevant) and 0s (not relevant) in rank order
            k: Number of top results to consider (default 3)

        Returns:
            Precision score (0-1)
        """
        if not relevant_chunks or k == 0:
            return 0.0

        top_k = relevant_chunks[:k]
        relevant_count = sum(top_k)
        return relevant_count / len(top_k)

    @staticmethod
    def calculate_mrr(relevant_chunks: List[int]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR).
        Position of first relevant item (1-indexed).

        Args:
            relevant_chunks: List of 1s (relevant) and 0s (not relevant)

        Returns:
            MRR score (0-1)
        """
        for rank, is_relevant in enumerate(relevant_chunks, start=1):
            if is_relevant:
                return 1.0 / rank

        return 0.0  # No relevant item found

    @staticmethod
    def calculate_ndcg(
        relevance_scores: List[float], ideal_scores: List[float], k: int = 3
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain (NDCG).

        Args:
            relevance_scores: Relevance scores (0-1) for each result
            ideal_scores: Perfect relevance scores for normalization
            k: Number of top results to consider

        Returns:
            NDCG score (0-1)
        """
        def dcg(scores):
            """Calculate Discounted Cumulative Gain."""
            dcg_sum = 0.0
            for rank, score in enumerate(scores, start=1):
                dcg_sum += score / (1.0 + __import__('math').log2(rank))
            return dcg_sum

        top_k_relevance = relevance_scores[:k]
        top_k_ideal = ideal_scores[:k]

        dcg_actual = dcg(top_k_relevance)
        dcg_ideal = dcg(top_k_ideal)

        if dcg_ideal == 0:
            return 0.0

        return dcg_actual / dcg_ideal


class HallucinationMetricsCalculator:
    """Calculate hallucination risk and grounding metrics."""

    @staticmethod
    def calculate_grounding_score(
        answer_tokens: Set[str], context_tokens: Set[str]
    ) -> float:
        """
        Calculate grounding score: % of answer tokens that appear in context.

        Returns:
            Score 0-1 (1.0 = fully grounded, 0.0 = no overlap)
        """
        if not answer_tokens:
            return 1.0  # Empty answer is trivially grounded

        grounded = answer_tokens.intersection(context_tokens)
        return len(grounded) / len(answer_tokens)

    @staticmethod
    def calculate_semantic_consistency(
        answer_tokens: Counter, context_tokens: Counter
    ) -> float:
        """
        Calculate semantic consistency via token frequency matching.

        Returns:
            Score 0-1 (how well token distributions match)
        """
        if not answer_tokens or not context_tokens:
            return 0.5  # Neutral if empty

        # Compute cosine similarity of token frequency vectors
        intersection = set(answer_tokens.keys()).intersection(context_tokens.keys())

        if not intersection:
            return 0.0  # No token overlap = no consistency

        numerator = sum(
            answer_tokens[token] * context_tokens[token] for token in intersection
        )
        denominator = (
            sum(v**2 for v in answer_tokens.values()) ** 0.5
            * sum(v**2 for v in context_tokens.values()) ** 0.5
        )

        if denominator == 0:
            return 0.0

        return min(1.0, numerator / denominator)

    @staticmethod
    def calculate_confidence_score(
        grounding_score: float,
        semantic_consistency: float,
        context_count: int,
        rrf_scores: List[float],
    ) -> float:
        """
        Calculate overall confidence score combining multiple signals.

        Args:
            grounding_score: Grounding metric (0-1)
            semantic_consistency: Semantic match metric (0-1)
            context_count: Number of context chunks used
            rrf_scores: RRF scores from each chunk

        Returns:
            Confidence score (0-1)
        """
        # Base score from grounding and consistency
        base_score = (grounding_score * 0.6 + semantic_consistency * 0.4)

        # Boost for multiple context sources
        context_boost = min(0.2, context_count * 0.05)

        # Boost for high-quality RRF scores
        rrf_boost = 0.0
        if rrf_scores:
            avg_rrf = sum(rrf_scores) / len(rrf_scores)
            rrf_boost = min(0.15, avg_rrf * 2.0)

        confidence = min(1.0, base_score + context_boost + rrf_boost)
        return confidence

    @staticmethod
    def calculate_hallucination_risk(confidence_score: float) -> float:
        """
        Calculate hallucination risk as inverse of confidence.

        Returns:
            Risk score (0-1, where 1.0 = high risk)
        """
        return 1.0 - confidence_score

    @staticmethod
    def calculate_safety_verdict(
        confidence_score: float, hallucination_risk: float
    ) -> str:
        """Determine safety classification."""
        if confidence_score >= 0.85 and hallucination_risk <= 0.15:
            return "safe"
        elif confidence_score >= 0.70 and hallucination_risk <= 0.30:
            return "caution"
        else:
            return "unsafe"


class QualityScoreCalculator:
    """Calculate overall quality score combining all metrics."""

    @staticmethod
    def calculate_overall_quality(
        precision_at_3: float,
        mrr_score: float,
        ndcg_score: float,
        keyword_coverage: float,
        confidence_score: float,
        hallucination_risk: float,
        grounding_score: float,
    ) -> Tuple[float, str]:
        """
        Calculate weighted overall quality score.

        Returns:
            (quality_score: 0-1, quality_grade: A+|A|B|C|D)
        """
        # Weighted combination of metrics
        retrieval_quality = (
            precision_at_3 * 0.25
            + mrr_score * 0.25
            + ndcg_score * 0.25
            + keyword_coverage * 0.25
        )

        generation_quality = (
            confidence_score * 0.5
            + (1.0 - hallucination_risk) * 0.25
            + grounding_score * 0.25
        )

        # Overall score: balance retrieval and generation
        overall = retrieval_quality * 0.4 + generation_quality * 0.6

        # Penalize for high hallucination risk
        if hallucination_risk > 0.3:
            overall *= 0.8
        elif hallucination_risk > 0.15:
            overall *= 0.9

        overall = min(1.0, max(0.0, overall))

        # Grade mapping
        if overall >= 0.95:
            grade = "A+"
        elif overall >= 0.90:
            grade = "A"
        elif overall >= 0.80:
            grade = "B"
        elif overall >= 0.70:
            grade = "C"
        else:
            grade = "D"

        return overall, grade
