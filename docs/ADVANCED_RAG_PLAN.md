# Advanced RAG Implementation Strategy: Maximum Accuracy & Reliability

This document outlines the phased strategy to maximize the efficiency of the RAG system.

## 1. Score Optimization Matrix

| Criterion | Goal Score | Strategic Implementation |
| :--- | :--- | :--- |
| **Retrieval Accuracy** | 25/25 | **Hybrid Search**: Fusing semantic (Qdrant) and lexical (Postgres) results using **Reciprocal Rank Fusion (RRF)**. |
| **Production Readiness** | 20/20 | **Metadata Filtering**: Ensuring queries are scoped (Dept/Category). Async API execution. |
| **Architecture Design** | 15/15 | **Modular RAG Pipeline**: Clean separation of Parser -> Embedder -> Searcher -> Generator. |
| **Hallucination Prevention** | 15/15 | **Confidence Guardrail**: Logic-based cutoff if RRF scores are low + Citation-enforced prompt. |
| **Innovation & Bonus** | 25/25 | **Cross-Encoder Reranking** and **RAG Comparison Dashboard** (Visual evidence of Hybrid superiority). |

---

## 2. Implementation Phases

### Phase 1: High-Precision Ingestion (Retrieval Focus)
*   **The Parser**: Extracting not just text, but nested metadata (Headings, Version, Department).
*   **Dual-Strategy Chunking**:
    *   *Baseline*: Fixed-size overlapping chunks.
    *   *Innovation*: **Semantic Recursive Splitter** that breaks text at topic shifts, ensuring a chunk never contains half a technical concept.
*   **Vector Space**: Normalizing embeddings for technical acronyms (e.g., K8s mapping).

### Phase 2: The Hybrid Fusion Engine (Accuracy Focus)
*   **Sparse Search**: Implementing **BM25** on PostgreSQL to catch exact error codes (e.g., `504 Gateway Timeout`).
*   **Dense Search**: Semantic matching on Qdrant.
*   **RRF Implementation**: Implementing the `1/(k+rank)` formula to merge disparate search scores into a single "Truth List".

### Phase 3: Reliability & Hallucination Guard (Guardrail Focus)
*   **Thresholding**: A logic gate that rejects retrieval results with a normalized score below 0.6.
*   **Source Citation Pipeline**: Mapping every sentence in the LLM response back to its `uuid` in Qdrant for 1-to-1 transparency.
*   **Context Scoping**: Automated injection of "Department" filters to eliminate noise from unrelated docs.

### Phase 4: Innovation & Analysis
*   **Innovation**: Building a **Retrieval Visualizer**—a small UI component that shows "Semantic Score" vs "Keyword Score" for each hit.
*   **Bonus**: Implement **Cohere Rerank** or a local Cross-Encoder to re-order the top 5 results for maximum relevance.

---

## 3. Work Distribution for this Phase
*   **Target**: `app/services/hybrid_engine.py`
*   **Target**: `app/core/rag_pipeline.py`
*   **Target**: `app/ingestion/semantic_parser.py`
