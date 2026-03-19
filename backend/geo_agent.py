import asyncio
import json
from tinyfish import AsyncTinyFish
from dotenv import load_dotenv

load_dotenv()

client = AsyncTinyFish()

PLATFORMS = {
    "perplexity": "https://perplexity.ai",
    "bing": "https://bing.com",
    "brave": "https://search.brave.com",
    "duckduckgo": "https://duckduckgo.com",
}

async def scan_platform(platform: str, brand: str) -> dict:
    try:
        response = await asyncio.wait_for(
            client.agent.run(
                url=PLATFORMS[platform],
                goal=f"Search for '{brand}' using the search bar. After results load, return a JSON object with these fields: platform ('{platform}'), brand ('{brand}'), mentioned (true or false), sentiment ('positive' or 'neutral' or 'negative'), context (one sentence about what the results say), snippet (first sentence copied from the results). Return only the JSON, nothing else."
            ),
            timeout=300
        )
        return response.result if response.result else {"platform": platform, "error": "no result"}
    except asyncio.TimeoutError:
        return {"platform": platform, "error": "timeout"}
    except Exception as e:
        return {"platform": platform, "error": str(e)}

async def scan_all(brand: str) -> list:
    tasks = [scan_platform(p, brand) for p in PLATFORMS]
    return await asyncio.gather(*tasks)
    