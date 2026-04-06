import asyncio
import os
import traceback
from dotenv import load_dotenv


async def test():
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY")
    print(f"API key loaded: {bool(key)}")

    # Lazy imports to avoid circular issues
    import geo_agent
    import synthesizer

    try:
        queries = geo_agent.generate_queries("Samsung")
        print(f"Generated queries: {queries}")

        print("Testing compute_score...")
        mock_results = [
            {
                "platform": "perplexity",
                "brand": "Samsung",
                "queries_tested": 3,
                "queries_with_mention": 1,
                "mention_rate": 33,
                "sentiment": "neutral",
                "best_query": None,
                "context": "Samsung appeared in 1 out of 3 category searches on perplexity",
                "snippet": "Test snippet",
                "query_results": [],
            }
        ]
        score = synthesizer.compute_score(mock_results, "Samsung")
        print("Score:", score)

    except Exception:
        print(f"Error:\n{traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test())
