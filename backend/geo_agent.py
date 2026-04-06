import asyncio
import json
import os
import re
from collections import Counter
from urllib.parse import quote_plus

from anthropic import Anthropic
from dotenv import load_dotenv
from tinyfish import AsyncTinyFish

load_dotenv()

client = AsyncTinyFish()
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PLATFORMS = {
    "perplexity": "https://www.perplexity.ai/search?q=",
    "chatgpt": "https://chatgpt.com/?q=",
    "bing": "https://www.bing.com/search?q=",
}

# Timeouts
QUERY_TIMEOUT = 120          # per-query: 2 min (some platforms are slow)
PLATFORM_TIMEOUT = 300       # per-platform: 5 min (3 queries + retries)
MAX_RETRIES = 1              # retry failed/timeout queries once


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
        print(f"[generate_queries] fallback: {type(e).__name__}")
        return ["best products in this category 2025", "top brands comparison review", "most recommended options for everyday use"]


def validate_brand(brand: str) -> str:
    """Validate and sanitize brand name input."""
    brand = brand.strip()
    if not brand or len(brand) > 100:
        raise ValueError("Brand name must be 1-100 characters")
    if not re.match(r'^[a-zA-Z0-9\s\-\.&\'\u00C0-\u024F]+$', brand):
        raise ValueError("Brand name contains invalid characters")
    return brand


def _build_url(platform: str, query: str) -> str:
    """Build search URL with query embedded so the agent only reads results."""
    return PLATFORMS[platform] + quote_plus(query)


def _parse_agent_result(raw, query: str) -> dict:
    """Parse TinyFish agent result into a normalized dict.

    TinyFish returns results in multiple formats depending on the platform:
      - dict with mentioned/snippet directly: {"mentioned": true, "snippet": "..."}
      - dict wrapped: {"result": "```json\n{...}\n```"}
      - string: '{"mentioned": true, ...}'
      - string with markdown: '```json\n{"mentioned": true}\n```'
      - dict with narrative + embedded JSON: {"result": "some text... ```json\n{...}```"}
    """
    if not raw:
        return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral"}

    parsed = None

    # Case 1: raw is already a dict with "mentioned" key
    if isinstance(raw, dict) and "mentioned" in raw:
        parsed = raw

    # Case 2: raw is a dict with a "result" key containing a string
    elif isinstance(raw, dict) and "result" in raw:
        inner = raw["result"]
        if isinstance(inner, str):
            parsed = _extract_json_from_string(inner)
        elif isinstance(inner, dict) and "mentioned" in inner:
            parsed = inner

    # Case 3: raw is a string containing JSON
    elif isinstance(raw, str):
        parsed = _extract_json_from_string(raw)

    if not parsed or "mentioned" not in parsed:
        # Last resort: check if the raw text itself contains the brand name
        raw_str = json.dumps(raw) if isinstance(raw, dict) else str(raw)
        return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral"}

    return {
        "query": query,
        "mentioned": bool(parsed.get("mentioned", False)),
        "snippet": parsed.get("snippet"),
        "sentiment": parsed.get("sentiment", "neutral"),
    }


def _extract_json_from_string(text: str) -> dict | None:
    """Extract a JSON object from a string that may contain markdown fences or narrative."""
    # Strip markdown fences
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        # Find the last ``` block (narrative text often precedes the JSON)
        parts = text.split("```")
        for i in range(len(parts) - 1, 0, -1):
            candidate = parts[i].strip()
            if candidate.startswith("{"):
                text = candidate
                break
        else:
            text = parts[1].strip() if len(parts) > 1 else text

    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find a JSON object anywhere in the text
    match = re.search(r'\{[^{}]*"mentioned"\s*:\s*(true|false)[^{}]*\}', text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


async def _run_single_scan(platform: str, brand: str, query: str) -> dict:
    """Execute a single TinyFish scan (no retry logic)."""
    url = _build_url(platform, query)
    response = await asyncio.wait_for(
        client.agent.run(
            url=url,
            goal=f'Read this page. Is "{brand}" mentioned? JSON only: {{"mentioned": true, "snippet": "exact sentence", "sentiment": "positive/neutral/negative"}} or {{"mentioned": false, "snippet": null, "sentiment": "neutral"}}',
        ),
        timeout=QUERY_TIMEOUT,
    )
    return _parse_agent_result(response.result, query)


async def scan_single_query(platform: str, brand: str, query: str) -> dict:
    """Scan a single query on a platform with retry on failure."""
    last_error = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            result = await _run_single_scan(platform, brand, query)
            # If we got an actual result (not an error), return it
            if "error" not in result:
                if attempt > 0:
                    print(f"[retry] {platform}/{query[:30]}... succeeded on attempt {attempt + 1}")
                return result
        except asyncio.TimeoutError:
            last_error = "timeout"
            print(f"[timeout] {platform}/{query[:30]}... attempt {attempt + 1}/{1 + MAX_RETRIES}")
        except Exception as e:
            last_error = "scan_failed"
            print(f"[error] {platform}/{query[:30]}... attempt {attempt + 1}: {type(e).__name__}")

        # Brief pause before retry
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2)

    return {"query": query, "mentioned": False, "snippet": None, "sentiment": "neutral", "error": last_error or "failed"}


async def scan_platform(platform: str, brand: str, queries: list) -> dict:
    """Scan all queries for a single platform in parallel."""
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
    errors = [r for r in clean_results if r.get("error")]
    total_queries = len(queries)
    mention_rate = int((len(mentions) / total_queries) * 100) if total_queries > 0 else 0
    snippets = [r.get("snippet") for r in mentions if r.get("snippet")]

    # Determine sentiment from actual snippet content
    if mentions:
        sentiments = [r.get("sentiment", "neutral") for r in mentions if r.get("sentiment")]
        sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else "positive"
    elif errors and len(errors) == total_queries:
        sentiment = "neutral"  # all failed = unknown, not negative
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
        "errors": len(errors),
    }


async def scan_platform_with_timeout(platform: str, brand: str, queries: list) -> dict:
    try:
        return await asyncio.wait_for(scan_platform(platform, brand, queries), timeout=PLATFORM_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[platform_timeout] {platform} timed out after {PLATFORM_TIMEOUT}s")
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
            "errors": 3,
        }
