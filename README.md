# GEO Monitor

Most brands obsess over Google rankings. But when someone asks ChatGPT "what's the best running shoe?", does your brand show up?

GEO Monitor answers that question. It deploys parallel browser agents across AI search platforms to measure organic brand visibility — the new frontier of digital presence that most marketing teams aren't tracking yet.

## The problem it solves

AI search is replacing traditional search for millions of queries. Brands have no visibility into whether they appear in AI-generated answers. GEO Monitor gives them a score, a breakdown by platform, and concrete recommendations to improve.

## How it works

1. Enter any brand name
2. Claude generates 3 organic category queries a real user would type
3. 3 TinyFish agents navigate Perplexity, ChatGPT and Bing simultaneously
4. Each agent checks if the brand appears naturally in AI-generated results
5. Claude synthesizes results into a Brand Visibility Score (0–100) with platform breakdown and GEO recommendations

## Live app

https://geo-monitor-coral.vercel.app

## Stack

| Layer | Technology |
|---|---|
| Browser agents | TinyFish Web Agent API |
| AI processing | Anthropic Claude (claude-sonnet-4-6) |
| Backend | Python / FastAPI / SSE streaming |
| Frontend | Next.js 15 / TypeScript |
| Backend deploy | Railway |
| Frontend deploy | Vercel |

## Architecture

The backend exposes a single SSE endpoint `/api/scan/{brand}`. Results stream to the frontend in real time as each agent completes — no polling, no waiting for all platforms to finish before showing results.
Brand input → Claude query generation → 3 parallel TinyFish agents
↓                                         ↓
SSE stream ← FastAPI ← per-platform results as they arrive
↓
Next.js UI renders scores and snippets progressively

## Local setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Create `backend/.env`:
TINYFISH_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```bash
uvicorn server:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `localhost:3000`.

## Demo mode

Add `?demo=true` to any scan request to get instant pre-built results without consuming TinyFish credits — useful for presentations and testing the UI.
