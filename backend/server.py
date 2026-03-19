import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from geo_agent import scan_platform, PLATFORMS
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

@app.get("/api/scan/{brand}")
async def scan_brand(brand: str):
    async def stream():
        yield f"data: {json.dumps({'type': 'started', 'platforms': list(PLATFORMS.keys())})}\n\n"

        tasks = {p: asyncio.create_task(scan_platform(p, brand)) for p in PLATFORMS}
        results = []

        for platform, task in tasks.items():
            result = await task
            results.append(result)
            yield f"data: {json.dumps({'type': 'platform_done', 'platform': platform, 'result': result})}\n\n"

        score = compute_score(results, brand)
        yield f"data: {json.dumps({'type': 'complete', 'score': score})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.get("/")
def root():
    return {"status": "GEO Monitor API running"}