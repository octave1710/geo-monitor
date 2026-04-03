import asyncio
import json
from tinyfish import AsyncTinyFish
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = AsyncTinyFish()
claude = Anthropic()

PLATFORMS = {
    "perplexity": "https://perplexity.ai",
    "chatgpt": "https://chatgpt.com",
    "bing": "https://bing.com",
}

def generate_queries(brand: str) -> list:
    msg = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Generate 3 realistic search queries that someone would type when looking for products in the same category as '{brand}', WITHOUT mentioning the brand name.
Natural consumer queries only. Mix intents: best-of, comparison, recommendation.
Return ONLY a JSON array of 3 strings, no other text, no markdown.
Example for Nike: ["best running shoes 2025", "top athletic footwear brands", "most popular sneakers right now"]"""
        }]
    )
    return json.loads(msg.content[0].text)

async def scan_single_query(platform: str, brand: str, query: str) -> dict:
    try:
        response = await asyncio.wait_for(
            client.agent.run(
                url=PLATFORMS[platform],
                goal=f"""Search for '{query}' using the search bar. Wait for results to load. Check if '{brand}' is mentioned anywhere in the results. Return ONLY this JSON, no other text:
{{"query": "{query}", "mentioned": true or false, "snippet": "copy the exact sentence mentioning {brand}, or null if not mentioned"}}"""
            ),
            timeout=300
        )
        raw = response.result
        if not raw:
            return {"query": query, "mentioned": False, "snippet": None}
        if isinstance(raw, str):
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        return raw
    except asyncio.TimeoutError:
        return {"query": query, "mentioned": False, "snippet": None, "error": "timeout"}
    except Exception as e:
        return {"query": query, "mentioned": False, "snippet": None, "error": str(e)}

async def scan_platform(platform: str, brand: str, queries: list) -> dict:
    tasks = [scan_single_query(platform, brand, q) for q in queries]
    query_results = await asyncio.gather(*tasks)
    mentions = [r for r in query_results if r.get("mentioned")]
    mention_rate = int((len(mentions) / len(queries)) * 100)
    snippets = [r.get("snippet") for r in mentions if r.get("snippet")]
    return {
        "platform": platform,
        "brand": brand,
        "queries_tested": len(queries),
        "queries_with_mention": len(mentions),
        "mention_rate": mention_rate,
        "sentiment": "positive" if mention_rate >= 50 else "neutral" if mention_rate > 0 else "negative",
        "best_query": mentions[0].get("query") if mentions else None,
        "context": f"{brand} appeared in {len(mentions)} out of {len(queries)} category searches on {platform}",
        "snippet": snippets[0] if snippets else None
    }

async def scan_all(brand: str) -> dict:
    queries = generate_queries(brand)
    tasks = [scan_platform(p, brand, queries) for p in PLATFORMS]
    results = await asyncio.gather(*tasks)
    return {"queries": queries, "results": list(results)}
