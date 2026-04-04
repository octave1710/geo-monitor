import asyncio
import os
from server import app
import geo_agent
import synthesizer
import traceback
from dotenv import load_dotenv

async def test():
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY")
    print(f"API Key Load check: {key[:15]}... ({len(key) if key else 0} chars)")
    
    try:
        queries = geo_agent.generate_queries("Samsung")
        with open("raw_output.txt", "w") as f:
            f.write(f"SUCCESS QUERIES:\n{queries}\n\n")
        
        print("Testing compute_score...")
        mock_results = [{"platform": "perplexity", "mentions": True, "sentiment": "neutral", "snippet": "Test", "queries_tested": 3, "queries_with_mention": 1, "context": "...", "query_results": []}]
        score = synthesizer.compute_score(mock_results, "Samsung")
        with open("raw_output.txt", "a") as f:
            f.write(f"SUCCESS SCORE:\n{score}\n")
            
    except Exception as e:
        with open("raw_output.txt", "w") as f:
            f.write(f"Exception:\n{traceback.format_exc()}")

    print("\nTesting compute_score...")
    mock_results = [{"platform": "perplexity", "mentions": True, "sentiment": "neutral", "snippet": "Test snippet", "queries_tested": 3, "queries_with_mention": 1, "context": "...", "query_results": []}]
    try:
        score = synthesizer.compute_score(mock_results, "Samsung")
        print("Score:", score)
    except Exception as e:
        print(f"compute_score failed! Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
