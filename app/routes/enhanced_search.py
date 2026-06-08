"""
Enhanced search endpoint with full evaluation metrics and structured logging.
Implements confidence scoring, grounding validation, and performance tracking.
"""

import time
import uuid
from typing import List
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException
from app.models.enhanced_schemas import (
    SearchRequest,
    SearchResponse,
    ContextChunk,
    ProcessingMetrics,
    ProcessingStage,
    RetrievalMetrics,
    HallucinationMetrics,
    FactVerification,
    GroundingEvidence,
)
from app.utils.metrics_calculator import (
    RetrievalMetricsCalculator,
    HallucinationMetricsCalculator,
    QualityScoreCalculator,
)
from app.utils.json_logger import ExecutionLogger


router = APIRouter(prefix="/api/v1", tags=["search"])


# ============================================================================
# HELPER FUNCTIONS FOR METRICS CALCULATION
# ============================================================================


async def calculate_retrieval_metrics(
    query: str, context_chunks: List[ContextChunk]
) -> RetrievalMetrics:
    """
    Calculate retrieval quality metrics (Precision@3, MRR, NDCG, coverage).
    """
    if not context_chunks:
        return RetrievalMetrics(
            precision_at_3=0.0,
            mean_reciprocal_rank=0.0,
            ndcg_score=0.0,
            keyword_coverage=0.0,
            matched_terms=[],
            coverage_status="low",
        )

    # Combine all context into single text for coverage calculation
    combined_context = " ".join([chunk.text_content for chunk in context_chunks])
    coverage_score, matched_tokens = RetrievalMetricsCalculator.calculate_keyword_coverage(
        query, combined_context
    )

    # Assume relevance based on RRF scores (1 if score > threshold, 0 otherwise)
    relevance_threshold = 0.01
    relevant_chunks = [
        1 if chunk.rrf_score > relevance_threshold else 0
        for chunk in context_chunks
    ]

    # Calculate precision@3
    precision_at_3 = RetrievalMetricsCalculator.calculate_precision_at_k(
        relevant_chunks, k=3
    )

    # Calculate MRR
    mrr_score = RetrievalMetricsCalculator.calculate_mrr(relevant_chunks)

    # Calculate NDCG (use RRF scores as relevance)
    rrf_scores = [chunk.rrf_score for chunk in context_chunks]
    ideal_scores = sorted(rrf_scores, reverse=True)
    ndcg_score = RetrievalMetricsCalculator.calculate_ndcg(rrf_scores, ideal_scores, k=3)

    # Determine coverage status
    if coverage_score >= 0.8:
        coverage_status = "complete"
    elif coverage_score >= 0.5:
        coverage_status = "partial"
    else:
        coverage_status = "low"

    return RetrievalMetrics(
        precision_at_3=round(precision_at_3, 4),
        mean_reciprocal_rank=round(mrr_score, 4),
        ndcg_score=round(ndcg_score, 4),
        keyword_coverage=round(coverage_score, 4),
        matched_terms=matched_tokens,
        coverage_status=coverage_status,
    )


async def calculate_hallucination_metrics(
    answer: str, context_chunks: List[ContextChunk]
) -> HallucinationMetrics:
    """
    Calculate hallucination risk metrics (confidence, grounding, fact verification).
    """
    # Tokenize answer and context
    answer_tokens = RetrievalMetricsCalculator.tokenize(answer)
    context_tokens_set = RetrievalMetricsCalculator.tokenize(
        " ".join([chunk.text_content for chunk in context_chunks])
    )

    # Calculate grounding score
    grounding_score = HallucinationMetricsCalculator.calculate_grounding_score(
        answer_tokens, context_tokens_set
    )

    # Calculate semantic consistency
    answer_counter = Counter(RetrievalMetricsCalculator.tokenize(answer))
    context_counter = Counter(context_tokens_set)
    semantic_consistency = HallucinationMetricsCalculator.calculate_semantic_consistency(
        answer_counter, context_counter
    )

    # Calculate confidence score
    rrf_scores = [chunk.rrf_score for chunk in context_chunks]
    confidence_score = HallucinationMetricsCalculator.calculate_confidence_score(
        grounding_score=grounding_score,
        semantic_consistency=semantic_consistency,
        context_count=len(context_chunks),
        rrf_scores=rrf_scores,
    )

    # Calculate hallucination risk
    hallucination_risk = HallucinationMetricsCalculator.calculate_hallucination_risk(
        confidence_score
    )

    # Determine safety verdict
    safety_verdict = HallucinationMetricsCalculator.calculate_safety_verdict(
        confidence_score, hallucination_risk
    )

    # Build fact verification (simplified)
    grounding_evidence_list = [
        GroundingEvidence(
            fact=token,
            source_chunk_id=context_chunks[0].chunk_id if context_chunks else "unknown",
            confidence=grounding_score,
            match_type="exact" if token in context_tokens_set else "semantic",
        )
        for token in list(answer_tokens)[:10]  # Top 10 facts
    ]

    fact_verification = FactVerification(
        verified_facts=len(
            [e for e in grounding_evidence_list if e.match_type == "exact"]
        ),
        unverified_facts=len(
            [e for e in grounding_evidence_list if e.match_type == "semantic"]
        ),
        contradicted_facts=0,
        grounding_evidence=grounding_evidence_list,
        verification_status="complete",
    )

    return HallucinationMetrics(
        confidence_score=round(confidence_score, 4),
        hallucination_risk=round(hallucination_risk, 4),
        grounding_score=round(grounding_score, 4),
        fact_verification=fact_verification,
        semantic_consistency=round(semantic_consistency, 4),
        safety_verdict=safety_verdict,
    )


# ============================================================================
# MAIN ENHANCED SEARCH ENDPOINT
# ============================================================================


@router.post("/search", response_model=SearchResponse, tags=["RAG"])
async def enhanced_search(request: SearchRequest) -> SearchResponse:
    """
    Enhanced hybrid search endpoint with full evaluation metrics.

    Returns SearchResponse with:
    - Generated answer from LLM
    - Retrieved context chunks with extended metadata
    - Retrieval accuracy metrics (Precision@3, MRR, NDCG, coverage)
    - Hallucination prevention metrics (confidence, grounding, risk)
    - Performance breakdown across processing stages
    - Execution logs with request tracking
    """

    # Initialize request tracking
    request_id = str(uuid.uuid4())
    exec_logger = ExecutionLogger(request_id)
    stage_times = {}

    try:
        # Stage 1: Retrieve context
        exec_logger.start_stage("retrieval")
        start_retrieval = time.perf_counter()

        # Import orchestration function (adjust import path as needed)
        from app.services.orchestration import process_query

        # Execute pipeline
        orchestration_result = await process_query(request.user_query)

        retrieval_time = (time.perf_counter() - start_retrieval) * 1000
        exec_logger.end_stage("retrieval", status="success", duration_ms=retrieval_time)
        stage_times["retrieval"] = retrieval_time

        # Parse orchestration result into enhanced context chunks
        context_chunks = []
        if orchestration_result.citations:
            for rank, citation in enumerate(orchestration_result.citations, start=1):
                # Calculate relevance and coverage
                coverage_score, coverage_tokens = (
                    RetrievalMetricsCalculator.calculate_keyword_coverage(
                        request.user_query, citation.text_snippet
                    )
                )

                context_chunks.append(
                    ContextChunk(
                        rank=rank,
                        chunk_id=citation.chunk_id,
                        rrf_score=citation.relevance_score,
                        source_document=citation.document_name,
                        text_content=citation.text_snippet,
                        relevance_score=citation.relevance_score,
                        grounding_contribution=coverage_score,
                        coverage_tokens=coverage_tokens,
                    )
                )

        exec_logger.log_event(
            "context_retrieved",
            chunk_count=len(context_chunks),
            top_rrf_score=context_chunks[0].rrf_score if context_chunks else 0.0,
        )

        # Stage 2: Calculate retrieval metrics
        exec_logger.start_stage("metrics_calculation")
        start_metrics = time.perf_counter()

        retrieval_metrics = await calculate_retrieval_metrics(
            request.user_query, context_chunks
        )

        metrics_time = (time.perf_counter() - start_metrics) * 1000
        exec_logger.end_stage("metrics_calculation", status="success", duration_ms=metrics_time)
        stage_times["metrics_calculation"] = metrics_time

        # Stage 3: Calculate hallucination metrics
        exec_logger.start_stage("hallucination_analysis")
        start_hallucination = time.perf_counter()

        hallucination_metrics = await calculate_hallucination_metrics(
            orchestration_result.answer, context_chunks
        )

        hallucination_time = (time.perf_counter() - start_hallucination) * 1000
        exec_logger.end_stage(
            "hallucination_analysis", status="success", duration_ms=hallucination_time
        )
        stage_times["hallucination_analysis"] = hallucination_time

        # Stage 4: Calculate quality score
        exec_logger.start_stage("quality_scoring")
        start_quality = time.perf_counter()

        overall_quality, quality_grade = QualityScoreCalculator.calculate_overall_quality(
            precision_at_3=retrieval_metrics.precision_at_3,
            mrr_score=retrieval_metrics.mean_reciprocal_rank,
            ndcg_score=retrieval_metrics.ndcg_score,
            keyword_coverage=retrieval_metrics.keyword_coverage,
            confidence_score=hallucination_metrics.confidence_score,
            hallucination_risk=hallucination_metrics.hallucination_risk,
            grounding_score=hallucination_metrics.grounding_score,
        )

        quality_time = (time.perf_counter() - start_quality) * 1000
        exec_logger.end_stage("quality_scoring", status="success", duration_ms=quality_time)
        stage_times["quality_scoring"] = quality_time

        exec_logger.log_event(
            "quality_calculated",
            overall_quality=overall_quality,
            grade=quality_grade,
        )

        # Build processing metrics
        total_duration_ms = sum(stage_times.values())
        bottleneck_stage = max(stage_times, key=stage_times.get) if stage_times else None
        processing_metrics = ProcessingMetrics(
            total_duration_ms=round(total_duration_ms, 2),
            stages=[
                ProcessingStage(
                    stage_name=name,
                    duration_ms=round(duration, 2),
                    status="success",
                )
                for name, duration in stage_times.items()
            ],
            bottleneck_stage=bottleneck_stage,
            optimization_potential=round(
                max(stage_times.values()) / total_duration_ms if stage_times else 0, 2
            ),
        )

        exec_logger.log_event(
            "response_complete",
            total_duration_ms=round(total_duration_ms, 2),
            bottleneck=bottleneck_stage,
        )

        # Build final response
        response = SearchResponse(
            answer=orchestration_result.answer,
            context_chunks=context_chunks,
            request_id=request_id,
            timestamp=datetime.utcnow(),
            processing_metrics=processing_metrics,
            retrieval_metrics=retrieval_metrics,
            hallucination_metrics=hallucination_metrics,
            overall_quality_score=round(overall_quality, 4),
            quality_grade=quality_grade,
            execution_logs=exec_logger.get_logs() if request.include_logs else None,
        )

        return response

    except Exception as e:
        exec_logger.log_event("error", error_type=type(e).__name__, error_msg=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
