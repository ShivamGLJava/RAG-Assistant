"""
Lexical search service using keyword matching.
File-driven configuration with zero database dependencies.
"""

import re
from typing import List, Dict, Any
from config import FIXED_CHUNK_SIZE, MAX_LEXICAL_RESULTS


def keyword_search(query: str, top_n: int = None) -> List[Dict[str, Any]]:
    """
    Execute keyword-based lexical search on document corpus.
    Returns list of dictionaries with chunk_id, text_content, and metadata.
    Grounded in AWS.pdf and FAQs.pdf content.

    Args:
        query: User search query string
        top_n: Maximum number of results to return (default from config)

    Returns:
        List of matching chunks with chunk_id, text_content, and metadata
    """
    if top_n is None:
        top_n = MAX_LEXICAL_RESULTS

    query_tokens = set(re.findall(r'\w+', query.lower()))
    if not query_tokens:
        return []

    local_document_corpus = [
        {
            "chunk_id": "faq_001_seven_rs",
            "text_content": "A critical first step is collecting application portfolio data evaluated against the seven common migration strategies (7 Rs): refactor, replatform, repurchase, rehost, relocate, retain, and retire.",
            "metadata": {
                "source_document": "FAQs.pdf",
                "section": "Migration Strategies",
                "page": 6,
                "chunk_size": FIXED_CHUNK_SIZE
            }
        },
        {
            "chunk_id": "aws_001_iaas_paas_saas",
            "text_content": "Understanding the differences between Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS) provides different levels of control, flexibility, and management.",
            "metadata": {
                "source_document": "AWS.pdf",
                "section": "Cloud Computing Models",
                "page": 2,
                "chunk_size": FIXED_CHUNK_SIZE
            }
        },
        {
            "chunk_id": "faq_002_discovery_rules",
            "text_content": "When assessing if an application can be retired, you must confirm that workloads aren't dependent on it. Use discovery tooling to show connections initiated to a server scheduled for retirement.",
            "metadata": {
                "source_document": "FAQs.pdf",
                "section": "Network Auditing",
                "page": 6,
                "chunk_size": FIXED_CHUNK_SIZE
            }
        },
        {
            "chunk_id": "aws_002_global_infrastructure",
            "text_content": "The AWS Cloud infrastructure is built around Regions and Availability Zones (AZs). The AWS Cloud operates 42 AZs within 16 geographic Regions around the world to maximize fault tolerance.",
            "metadata": {
                "source_document": "AWS.pdf",
                "section": "Global Infrastructure",
                "page": 4,
                "chunk_size": FIXED_CHUNK_SIZE
            }
        },
        {
            "chunk_id": "faq_003_controlled_stops",
            "text_content": "In your migration plan, schedule time for a controlled stop. A controlled stop pauses the migration process to identify the potential for disruption if an application is retired by simulating the retirement.",
            "metadata": {
                "source_document": "FAQs.pdf",
                "section": "Application Lifecycle",
                "page": 8,
                "chunk_size": FIXED_CHUNK_SIZE
            }
        }
    ]

    matched_candidates = []

    for document in local_document_corpus:
        doc_tokens = set(re.findall(r'\w+', document["text_content"].lower()))
        intersection = query_tokens.intersection(doc_tokens)

        if intersection:
            document["metadata"]["lexical_score"] = float(len(intersection))
            matched_candidates.append(document)

    matched_candidates.sort(
        key=lambda x: x["metadata"].get("lexical_score", 0.0),
        reverse=True
    )

    return matched_candidates[:top_n]
