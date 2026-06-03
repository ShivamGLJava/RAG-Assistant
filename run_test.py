import asyncio
from app.main import search, QueryRequest


async def main():
    print("\n" + "=" * 80)
    print("Testing API Route Orchestration Loop")
    print("=" * 80 + "\n")

    mock_request = QueryRequest(user_query="How do I fix a 502 error and container CrashLoopBackOff anomalies?")

    response = await search(mock_request)

    print("ORCHESTRATED ENGINE RESPONSE ('answer' key payload):")
    print("-" * 80)
    print(response.answer)
    print("-" * 80)
    print("\nCONTEXT CHUNKS:")
    print("-" * 80)
    for chunk in response.context_chunks:
        print(f"Rank: {chunk.rank}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"RRF Score: {chunk.rrf_score}")
        print(f"Source Document: {chunk.source_document}")
        print()
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
