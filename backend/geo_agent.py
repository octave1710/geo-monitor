import asyncio
import json
import os
import re
from collections import Counter

from anthropic import Anthropic
from dotenv import load_dotenv
from tinyfish import AsyncTinyFish

load_dotenv()

client = AsyncTinyFish()
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PLATFORMS = {
    "perplexity": "https://perplexity.ai",
    "chatgpt": "https://chatgpt.com",
    "bing": "https://bing.com",
}

QUERY_TIMEOUT = 90
PLATFORM_TIMEOUT = 100


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
        parsed = json.loads(raw_text)
        if not isinstance(parsed, list) or len(parsed) != 3 or not all(isinstance(q, str) for q in parsed):
            raise ValueError(f"Unexpected query format: {parsed}")
        return parsed
    except Exception as e:
        print(f"Query generation fallback: {type(e).__name__}")
        return ["best products in this category 2025", "top brands comparison review", "most recommended options for everyday use"]


def validate_brand(brand: str) -> str:
    """Validate and sanitize brand name input."""
    brand = brand.strip()
    if not brand or len(brand) > 100:
        raise ValueError("Brand name must be 1-100 characters")
    if not re.match(r'^[a-zA-Z0-9\s\-\.&\'\u00C0-\u024F]+$', brand):
        raise ValueError("Brand name contains invalid characters")
    return brand


async def scan_single_query(platform: str, brand: str, query: str) -> dict:
    try:
        response = await asyncio.wait_for(
            client.agent.run(
                url=PLATFORMS[platform],
                goal=f"Search for '{query}'. When results fully load, read the ENTIRE response carefully. Check if '{brand}' is mentioned anywhere in the text. Return only JSON: {{\"mentioned\": true/false, \"snippet\": \"exact sentence mentioning {brand} or null\", \"sentiment\": \"positive or neutral or negative based on the tone of the mention\"}}"
            ),
            timeout=QUERY_TIMEOUT
        )
        raw = response.result
        if not raw:
            return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral"}
        if isinstance(raw, str):
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            return {
                "query": query,
                "mentioned": bool(result.get("mentioned", False)),
                "snippet": result.get("snippet"),
                "sentiment": result.get("sentiment", "neutral"),
            }
        return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral"}
    except asyncio.TimeoutError:
        return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral", "error": "timeout"}
    except Exception:
        return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral", "error": "scan_failed"}


async def scan_platform(platform: str, brand: str, queries: list) -> dict:
    query_results = await asyncio.gather(
        *[scan_single_query(platform, brand, q) for q in queries],
        return_exceptions=True
    )
    clean_results = []
    for i, r in enumerate(query_results):
        if isinstance(r, Exception):
            clean_results.append({"query": queries[i], "mentioned": False, "snippet": None, "sentiment": "neutral", "error": "exception"})
        else:
            clean_results.append(r)

    mentions = [r for r in clean_results if r.get("mentioned")]
    total_queries = len(queries)
    mention_rate = int((len(mentions) / total_queries) * 100) if total_queries > 0 else 0
    snippets = [r.get("snippet") for r in mentions if r.get("snippet")]

    # Determine sentiment from actual snippet content
    if mentions:
        sentiments = [r.get("sentiment", "neutral") for r in mentions if r.get("sentiment")]
        sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else "positive"
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
        return await asyncio.wait_for(scan_platform(platform, brand, queries), timeout=PLATFORM_TIMEOUT)
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
