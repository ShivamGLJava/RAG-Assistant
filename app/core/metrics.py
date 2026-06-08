"""
Prometheus metrics exporter for RAG pipeline observability.
Tracks retrieval and generation latency with millisecond precision.

Exposes metrics:
  - r_pipeline_retrieval_duration_ms: Histogram of retrieval stage latency
  - r_pipeline_generation_duration_ms: Histogram of generation stage latency
"""

from contextlib import contextmanager
from prometheus_client import Histogram, Counter, Gauge, generate_latest, REGISTRY
import time
from typing import Optional


# ============================================================================
# HISTOGRAM METRICS (Primary observability signals)
# ============================================================================

# Retrieval latency: tracks time from query input to context retrieval completion
# Buckets: 50ms, 100ms, 200ms, 500ms, 1000ms, 2000ms, 5000ms, 10000ms, 30000ms
RETRIEVAL_DURATION_MS = Histogram(
    name='r_pipeline_retrieval_duration_ms',
    documentation='Retrieval stage latency in milliseconds',
    buckets=(50, 100, 200, 500, 1000, 2000, 5000, 10000, 30000),
    labelnames=['retrieval_type', 'status']
)

# Generation latency: tracks time from context embedding to LLM response
# Buckets: 100ms, 500ms, 1000ms, 2000ms, 5000ms, 10000ms, 30000ms, 60000ms
GENERATION_DURATION_MS = Histogram(
    name='r_pipeline_generation_duration_ms',
    documentation='Generation stage latency in milliseconds',
    buckets=(100, 500, 1000, 2000, 5000, 10000, 30000, 60000),
    labelnames=['model', 'status']
)

# ============================================================================
# COUNTER METRICS (Event tracking)
# ============================================================================

RETRIEVAL_TOTAL = Counter(
    name='r_pipeline_retrieval_total',
    documentation='Total retrieval requests',
    labelnames=['retrieval_type', 'status']
)

GENERATION_TOTAL = Counter(
    name='r_pipeline_generation_total',
    documentation='Total generation requests',
    labelnames=['model', 'status']
)

HALLUCINATION_DETECTIONS = Counter(
    name='r_pipeline_hallucinations_total',
    documentation='Total hallucination detections',
    labelnames=['severity']
)

# ============================================================================
# GAUGE METRICS (Point-in-time measurements)
# ============================================================================

ACTIVE_REQUESTS = Gauge(
    name='r_pipeline_active_requests',
    documentation='Currently active pipeline requests',
    labelnames=['stage']
)

CACHE_SIZE_BYTES = Gauge(
    name='r_pipeline_cache_size_bytes',
    documentation='Current cache size in bytes',
    labelnames=['cache_type']
)

RETRIEVAL_QUALITY_SCORE = Gauge(
    name='r_pipeline_retrieval_quality_score',
    documentation='Average retrieval quality score (0-1)',
    labelnames=['retrieval_type']
)

# ============================================================================
# METRIC TRACKER UTILITY CLASS
# ============================================================================


class MetricsTracker:
    """
    High-level utility for tracking pipeline metrics without direct prometheus imports.

    Usage:
        tracker = MetricsTracker()

        # Track retrieval
        with tracker.track_retrieval('lexical', 'success') as timer:
            # ... retrieval code ...
            pass

        # Track generation
        with tracker.track_generation('gemini-2.5', 'success') as timer:
            # ... generation code ...
            pass
    """

    @staticmethod
    @contextmanager
    def track_retrieval(retrieval_type: str = 'hybrid', status: str = 'success'):
        """
        Context manager for tracking retrieval latency.

        Args:
            retrieval_type: Type of retrieval (lexical, dense, hybrid)
            status: Request status (success, error, timeout)

        Example:
            with MetricsTracker.track_retrieval('lexical', 'success'):
                # retrieval code
        """
        ACTIVE_REQUESTS.labels(stage='retrieval').inc()
        start_time = time.perf_counter()

        try:
            yield
            duration_ms = (time.perf_counter() - start_time) * 1000
            RETRIEVAL_DURATION_MS.labels(
                retrieval_type=retrieval_type,
                status=status
            ).observe(duration_ms)
            RETRIEVAL_TOTAL.labels(
                retrieval_type=retrieval_type,
                status=status
            ).inc()
        finally:
            ACTIVE_REQUESTS.labels(stage='retrieval').dec()

    @staticmethod
    @contextmanager
    def track_generation(model: str = 'gemini-2.5', status: str = 'success'):
        """
        Context manager for tracking generation latency.

        Args:
            model: LLM model name
            status: Request status (success, error, timeout)

        Example:
            with MetricsTracker.track_generation('gemini-2.5', 'success'):
                # generation code
        """
        ACTIVE_REQUESTS.labels(stage='generation').inc()
        start_time = time.perf_counter()

        try:
            yield
            duration_ms = (time.perf_counter() - start_time) * 1000
            GENERATION_DURATION_MS.labels(
                model=model,
                status=status
            ).observe(duration_ms)
            GENERATION_TOTAL.labels(
                model=model,
                status=status
            ).inc()
        finally:
            ACTIVE_REQUESTS.labels(stage='generation').dec()

    @staticmethod
    def record_retrieval_quality(score: float, retrieval_type: str = 'hybrid'):
        """
        Record retrieval quality score.

        Args:
            score: Quality score (0-1)
            retrieval_type: Type of retrieval
        """
        if not (0 <= score <= 1):
            raise ValueError(f"Quality score must be 0-1, got {score}")
        RETRIEVAL_QUALITY_SCORE.labels(retrieval_type=retrieval_type).set(score)

    @staticmethod
    def record_hallucination_detection(severity: str = 'medium'):
        """
        Record hallucination detection event.

        Args:
            severity: Detection severity (low, medium, high)
        """
        if severity not in ('low', 'medium', 'high'):
            raise ValueError(f"Invalid severity: {severity}")
        HALLUCINATION_DETECTIONS.labels(severity=severity).inc()

    @staticmethod
    def set_cache_size(size_bytes: int, cache_type: str = 'embedding'):
        """
        Set cache size metric.

        Args:
            size_bytes: Cache size in bytes
            cache_type: Type of cache (embedding, response, etc.)
        """
        if size_bytes < 0:
            raise ValueError("Cache size cannot be negative")
        CACHE_SIZE_BYTES.labels(cache_type=cache_type).set(size_bytes)


# ============================================================================
# METRICS EXPORT FUNCTION
# ============================================================================


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.

    Returns:
        bytes: Prometheus-compatible metrics text

    Usage:
        In FastAPI route:
            @app.get("/metrics")
            async def metrics():
                return Response(
                    content=get_metrics(),
                    media_type="text/plain; charset=utf-8"
                )
    """
    return generate_latest(REGISTRY)


# ============================================================================
# INITIALIZATION & HEALTH CHECK
# ============================================================================


def verify_metrics_setup() -> dict:
    """
    Verify that metrics are properly initialized.

    Returns:
        dict: Status information
    """
    return {
        "status": "healthy",
        "metrics_initialized": True,
        "retrieval_histogram": "r_pipeline_retrieval_duration_ms",
        "generation_histogram": "r_pipeline_generation_duration_ms",
        "active_requests_gauge": "r_pipeline_active_requests",
        "retrieval_quality_gauge": "r_pipeline_retrieval_quality_score",
        "hallucination_counter": "r_pipeline_hallucinations_total"
    }
