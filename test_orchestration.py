"""
Test script for Engineer 5 orchestration components.
Tests mock RRF, firewall, and orchestration without requiring Ollama.
"""

import sys
import os
import asyncio

# Add current directory to path to avoid __init__.py imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only our new modules (don't import app.services to avoid __init__.py)
from app.services.mock_rrf import MockRRFEngine
from app.services.grounding import HallucinationFirewall
from app.services.orchestration import QueryOrchestrator


def test_mock_rrf():
    """Test mock RRF results generation."""
    print("\n" + "="*70)
    print("TEST 1: Mock RRF Results Generation")
    print("="*70)

    test_queries = [
        "How do I fix a CrashLoopBackOff error?",
        "What causes a 502 Bad Gateway?",
        "How do I resolve ImagePullBackOff?",
        "Something not in knowledge base"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = MockRRFEngine.search(query, top_n=3)
        print(f"  ✓ Retrieved {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['metadata']['source_document']} (score: {result['rrf_score']:.2f})")


def test_hallucination_firewall():
    """Test hallucination firewall logic."""
    print("\n" + "="*70)
    print("TEST 2: Hallucination Firewall")
    print("="*70)

    # Test case 1: Good confidence
    print("\nTest 2.1: High confidence results")
    results = MockRRFEngine.search("CrashLoopBackOff", top_n=3)
    should_call, chunks = HallucinationFirewall.should_call_llm(results)
    print(f"  Top score: {results[0]['rrf_score']:.2f}")
    print(f"  Firewall decision: {'ALLOW' if should_call else 'BLOCK'}")
    assert should_call, "Should allow high confidence queries"
    print("  ✓ Correctly allowed high-confidence query")

    # Test case 2: Low confidence
    print("\nTest 2.2: Low confidence results")
    low_conf_results = [
        {
            "chunk_id": "test_chunk",
            "text_content": "Barely relevant text",
            "metadata": {"source_document": "test.md"},
            "rrf_score": 0.05
        }
    ]
    should_call, chunks = HallucinationFirewall.should_call_llm(low_conf_results)
    print(f"  Top score: {low_conf_results[0]['rrf_score']:.2f}")
    print(f"  Firewall decision: {'ALLOW' if should_call else 'BLOCK'}")
    assert not should_call, "Should block low confidence queries"
    print("  ✓ Correctly blocked low-confidence query")

    # Test case 3: No results
    print("\nTest 2.3: No results")
    should_call, chunks = HallucinationFirewall.should_call_llm([])
    print(f"  Results: 0")
    print(f"  Firewall decision: {'ALLOW' if should_call else 'BLOCK'}")
    assert not should_call, "Should block when no results"
    print("  ✓ Correctly blocked query with no results")


def test_confidence_labels():
    """Test confidence label generation."""
    print("\n" + "="*70)
    print("TEST 3: Confidence Labels")
    print("="*70)

    scores = [0.05, 0.2, 0.5, 0.8, 0.95]
    for score in scores:
        label = HallucinationFirewall.get_confidence_label(score)
        print(f"  Score {score:.2f}: {label}")


async def test_orchestration():
    """Test full orchestration pipeline."""
    print("\n" + "="*70)
    print("TEST 4: Orchestration Pipeline (without Ollama)")
    print("="*70)

    orchestrator = QueryOrchestrator(use_mock_rrf=True)

    # Test query
    query = "How do I fix a 502 error?"
    print(f"\nQuery: {query}")

    # Get search results
    results = orchestrator._get_search_results(query)
    print(f"✓ Retrieved {len(results)} chunks")

    # Check firewall
    can_answer, chunks = HallucinationFirewall.should_call_llm(results)
    print(f"✓ Firewall decision: {'ALLOW' if can_answer else 'BLOCK'}")

    if can_answer:
        # Format citations
        citations = orchestrator._format_citations(chunks)
        print(f"✓ Formatted {len(citations)} citations")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {citation.document_name} (chunk: {citation.chunk_id}, score: {citation.relevance_score:.2f})")


def test_no_results_scenario():
    """Test scenario where no results are found."""
    print("\n" + "="*70)
    print("TEST 5: No Results Scenario")
    print("="*70)

    orchestrator = QueryOrchestrator(use_mock_rrf=True)

    # Query that might have low results
    results = orchestrator._get_search_results("Random gibberish query xyz")
    print(f"Results retrieved: {len(results)}")

    if results:
        can_answer, chunks = HallucinationFirewall.should_call_llm(results)
        print(f"Firewall would: {'ALLOW' if can_answer else 'BLOCK'}")
    else:
        print("✓ No results - would return fallback message")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ENGINEER 5 ORCHESTRATION TESTS")
    print("="*70)

    try:
        # Test 1: Mock RRF
        test_mock_rrf()

        # Test 2: Firewall
        test_hallucination_firewall()

        # Test 3: Confidence labels
        test_confidence_labels()

        # Test 4: Orchestration
        asyncio.run(test_orchestration())

        # Test 5: No results
        test_no_results_scenario()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nNext steps:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Start backend: python -m uvicorn app.main:app --reload")
        print("  3. Test endpoint: curl -X POST http://localhost:8000/api/v1/chat")
        print("  4. Visit React app: http://localhost:3000")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
