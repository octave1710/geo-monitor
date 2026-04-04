import asyncio
import json
from tinyfish import AsyncTinyFish
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = AsyncTinyFish()
import os
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PLATFORMS = {
    "perplexity": "https://perplexity.ai",
    "chatgpt": "https://chatgpt.com",
    "bing": "https://bing.com",
}

def generate_queries(brand: str) -> list:
    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Generate 3 search queries for the general product CATEGORY that '{brand}' operates in.

STRICT RULES:
- Do NOT mention '{brand}' or ANY of its product names, sub-brands, or trademarks
  (e.g. for Apple: no "iPhone", "MacBook", "iPad", "AirPods"; for Nike: no "Air Max", "Jordan", "Dunk")
- Use ONLY generic category terms like "best smartphones", "top running shoes", etc.
- Mix intents: 1 "best of" ranking, 1 comparison/recommendation, 1 general category search
- Queries should sound like a real consumer typing into a search engine

Return ONLY a JSON array of 3 strings, no other text, no markdown.
Example for Nike: ["best running shoes 2025", "top athletic footwear brands compared", "most comfortable sneakers for daily wear"]"""
        }]
    )
        raw_text = msg.content[0].text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"Query generation fallback due to error: {e}")
        return ["best products in this category 2025", "top brands comparison review", "most recommended options for everyday use"]

async def scan_single_query(platform: str, brand: str, query: str) -> dict:
    try:
        response = await asyncio.wait_for(
            client.agent.run(
                url=PLATFORMS[platform],
                goal=f"Search for '{query}'. When results fully load, read the ENTIRE response carefully. Check if '{brand}' is mentioned anywhere in the text. Return only JSON: {{\"mentioned\": true/false, \"snippet\": \"exact sentence mentioning {brand} or null\", \"sentiment\": \"positive or neutral or negative based on the tone of the mention\"}}"
            ),
            timeout=90
        )
        raw = response.result
        if not raw:
            return {"query": query, "mentioned": False, "snippet": None}
        if isinstance(raw, str):
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            result.setdefault("query", query)
            return result
        return raw
    except asyncio.TimeoutError:
        return {"query": query, "mentioned": False, "snippet": None, "error": "timeout"}
    except Exception as e:
        return {"query": query, "mentioned": False, "snippet": None, "error": str(e)}

async def scan_platform(platform: str, brand: str, queries: list) -> dict:
    query_results = await asyncio.gather(
        *[scan_single_query(platform, brand, q) for q in queries],
        return_exceptions=True
    )
    # Filter out exceptions, treat them as no-mention
    clean_results = []
    for i, r in enumerate(query_results):
        if isinstance(r, Exception):
            clean_results.append({"query": queries[i], "mentioned": False, "snippet": None, "error": str(r)})
        else:
            clean_results.append(r)

    mentions = [r for r in clean_results if r.get("mentioned")]
    total_queries = len(queries)
    mention_rate = int((len(mentions) / total_queries) * 100)
    snippets = [r.get("snippet") for r in mentions if r.get("snippet")]

    # Determine sentiment from actual snippet content when available
    if mentions:
        sentiments = [r.get("sentiment", "neutral") for r in mentions if r.get("sentiment")]
        if sentiments:
            from collections import Counter
            sentiment = Counter(sentiments).most_common(1)[0][0]
        else:
            sentiment = "positive"
    else:
        sentiment = "negative"

    return {
        "platform": platform,
        "brand": brand,
        "queries_tested": total_queries,
        "queries_with_mention": len(mentions),
        "mention_rate": mention_rate,
        "sentiment": sentiment,
        "best_query": mentions[0].get("query") if mentions else None,
        "context": f"{brand} appeared in {len(mentions)} out of {total_queries} category searches on {platform}",
        "snippet": snippets[0] if snippets else None,
        "query_results": clean_results,
    }

async def scan_platform_with_timeout(platform: str, brand: str, queries: list) -> dict:
    try:
        return await asyncio.wait_for(scan_platform(platform, brand, queries), timeout=100)
    except asyncio.TimeoutError:
        return {
            "platform": platform,
            "brand": brand,
            "queries_tested": 0,
            "queries_with_mention": 0,
            "mention_rate": 0,
            "sentiment": "neutral",
            "best_query": None,
            "context": "Platform scan timed out",
            "snippet": None,
            "query_results": [],
        }

async def scan_all(brand: str) -> dict:
    queries = generate_queries(brand)
    tasks = [scan_platform_with_timeout(p, brand, queries) for p in PLATFORMS]
    results = await asyncio.gather(*tasks)
    return {"queries": queries, "results": list(results)}
