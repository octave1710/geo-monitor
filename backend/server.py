import asyncio
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from geo_agent import scan_platform_with_timeout, generate_queries, PLATFORMS
from synthesizer import compute_score
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_QUERIES = [
    "best running shoes 2025",
    "top athletic footwear brands",
    "most comfortable sneakers for daily use",
]

DEMO_PLATFORMS = [
    {
        "platform": "perplexity",
        "mention_rate": 33,
        "sentiment": "neutral",
        "snippet": "Nike React Infinity Run Flyknit recommended for daily training.",
        "queries_tested": 3,
        "queries_with_mention": 1,
        "context": "Nike appeared in 1 out of 3 category searches on perplexity",
        "query_results": [
            {"query": "best running shoes 2025", "mentioned": True, "snippet": "Nike React Infinity Run Flyknit recommended for daily training."},
            {"query": "top athletic footwear brands", "mentioned": False, "snippet": None},
            {"query": "most comfortable sneakers for daily use", "mentioned": False, "snippet": None},
        ],
    },
    {
        "platform": "chatgpt",
        "mention_rate": 66,
        "sentiment": "positive",
        "snippet": "Nike Air Max 270 consistently ranks among top athletic shoes.",
        "queries_tested": 3,
        "queries_with_mention": 2,
        "context": "Nike appeared in 2 out of 3 category searches on chatgpt",
        "query_results": [
            {"query": "best running shoes 2025", "mentioned": True, "snippet": "Nike Air Max 270 consistently ranks among top athletic shoes."},
            {"query": "top athletic footwear brands", "mentioned": True, "snippet": "Nike, Adidas, and New Balance lead the athletic footwear market in 2025."},
            {"query": "most comfortable sneakers for daily use", "mentioned": False, "snippet": None},
        ],
    },
    {
        "platform": "bing",
        "mention_rate": 100,
        "sentiment": "positive",
        "snippet": "Nike leads comfort rankings across major sport retailers.",
        "queries_tested": 3,
        "queries_with_mention": 3,
        "context": "Nike appeared in 3 out of 3 category searches on bing",
        "query_results": [
            {"query": "best running shoes 2025", "mentioned": True, "snippet": "Nike Pegasus 41 tops the list of best running shoes for 2025."},
            {"query": "top athletic footwear brands", "mentioned": True, "snippet": "Nike leads comfort rankings across major sport retailers."},
            {"query": "most comfortable sneakers for daily use", "mentioned": True, "snippet": "The Nike Air Force 1 remains a top pick for all-day comfort."},
        ],
    },
]

DEMO_SCORE = {
    "visibility_score": 72,
    "dominant_sentiment": "positive",
    "platforms_present": ["chatgpt", "bing"],
    "platforms_absent": [],
    "summary": "Brand present in 2 out of 3 AI platforms with positive sentiment. Strong Bing presence.",
    "platform_analyses": [
        {
            "platform": "perplexity",
            "verdict": "weak",
            "analysis": "Nike only appeared in 1 of 3 category searches. Perplexity tends to cite academic and review sources — the brand may lack structured data in those domains.",
        },
        {
            "platform": "chatgpt",
            "verdict": "moderate",
            "analysis": "Nike was mentioned in 2 of 3 searches with positive framing. ChatGPT positioned Nike alongside competitors, suggesting good but not dominant visibility.",
        },
        {
            "platform": "bing",
            "verdict": "strong",
            "analysis": "Nike appeared in all 3 category searches with strong positive sentiment. Bing Copilot clearly pulls Nike data from retail and review aggregators.",
        },
    ],
    "geo_recommendations": [
        "Optimize for Perplexity citation format",
        "Build FAQ pages targeting AI search queries",
        "Increase presence on Reddit and forums indexed by AI platforms",
    ],
}


@app.get("/api/scan/{brand}")
async def scan_brand(brand: str, demo: bool = Query(default=False)):
    async def stream_demo():
        yield f"data: {json.dumps({'type': 'started', 'platforms': list(PLATFORMS.keys())})}\n\n"

        yield f"data: {json.dumps({'type': 'queries', 'queries': DEMO_QUERIES})}\n\n"

        for p in DEMO_PLATFORMS:
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps({'type': 'platform_done', 'result': p})}\n\n"

        yield f"data: {json.dumps({'type': 'complete', 'score': DEMO_SCORE})}\n\n"

    async def stream():
        yield f"data: {json.dumps({'type': 'started', 'platforms': list(PLATFORMS.keys())})}\n\n"

        queries = generate_queries(brand)
        yield f"data: {json.dumps({'type': 'queries', 'queries': queries})}\n\n"

        tasks = {p: asyncio.create_task(scan_platform_with_timeout(p, brand, queries)) for p in PLATFORMS}

        results = []
        pending = set(tasks.values())

        while pending:
            done, pending = await asyncio.wait(pending, timeout=15, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                result = await task
                results.append(result)
                yield f"data: {json.dumps({'type': 'platform_done', 'result': result})}\n\n"
            if pending:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

        score = compute_score(results, brand)
        yield f"data: {json.dumps({'type': 'complete', 'score': score})}\n\n"

    return StreamingResponse(
        stream_demo() if demo else stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/")
def root():
    return {"status": "GEO Monitor API running"}