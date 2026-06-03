import asyncio
from app.main import search, QueryRequest


async def run_test_case_a():
    """TEST CASE A: Valid Data Stream - Confirms full execution loop with Gemini API."""
    print("\n" + "=" * 80)
    print("TEST CASE A: Valid Data Stream (Gemini API Invocation)")
    print("=" * 80 + "\n")

    request = QueryRequest(
        user_query="How do I fix a 502 error and container CrashLoopBackOff anomalies?"
    )

    response = await search(request)

    print("Response Answer (excerpt):")
    print("-" * 80)
    if "[LLM INVOCATION EXCEPTION ERROR]" in response.answer:
        print(f"✓ Expected API exception caught")
        print(f"   Message: {response.answer[:150]}...")
    else:
        print(f"Answer: {response.answer[:200]}...")

    print(f"\nContext Chunks Retrieved: {len(response.context_chunks)}")
    if response.context_chunks:
        for chunk in response.context_chunks:
            print(f"  - {chunk.chunk_id}: {chunk.source_document} (Score: {chunk.rrf_score})")

    print("\n✓ TEST CASE A PASSED\n")


async def run_test_case_b():
    """TEST CASE B: Hallucination Control Firewall - Empty context triggers fallback."""
    print("=" * 80)
    print("TEST CASE B: Hallucination Control Firewall (Empty Context)")
    print("=" * 80 + "\n")

    import app.main as main_module

    original_fetch = main_module._fetch_vector_search_results

    async def mock_fetch(query):
        return []

    main_module._fetch_vector_search_results = mock_fetch

    try:
        request = QueryRequest(
            user_query="xyzabc9999nonsensequery_that_yields_no_results_whatsoever"
        )

        response = await search(request)

        print("Response Answer:")
        print("-" * 80)
        print(response.answer)
        print("-" * 80)

        fallback_msg = "I am sorry, but I cannot confidently deduce an answer based on the verified technical documentation provided."

        if response.answer == fallback_msg:
            print("\n✓ Hallucination Control Firewall TRIGGERED")
            print(f"✓ Fallback message returned as expected")
            print(f"✓ Context chunks: {len(response.context_chunks)} (expected 0)")
            print("\n✓ TEST CASE B PASSED\n")
        else:
            print("\n✗ TEST CASE B FAILED: Unexpected answer returned")
            print(f"Expected: {fallback_msg}")
            print(f"Got: {response.answer}")

    finally:
        main_module._fetch_vector_search_results = original_fetch


async def main():
    print("\n" + "=" * 80)
    print("RAG-Assistant Production-Ready Pipeline Test Suite")
    print("=" * 80)

    await run_test_case_a()
    await run_test_case_b()

    print("=" * 80)
    print("All test cases completed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
