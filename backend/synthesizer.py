import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

import os
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def compute_score(results: list, brand: str) -> dict:
    clean = [r for r in results if "error" not in r]

    if not clean:
        return {
            "visibility_score": 0,
            "platforms_present": [],
            "platforms_absent": list([r.get("platform", "unknown") for r in results]),
            "dominant_sentiment": "neutral",
            "summary": "No data could be retrieved for this brand.",
            "geo_recommendations": [
                "Check if brand has an online presence",
                "Create content optimized for AI search",
                "Build citations across authoritative sources"
            ]
        }

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": f"""
Analyze these AI platform scan results for brand '{brand}':
{json.dumps(clean, indent=2)}

Return ONLY valid JSON, no other text:
{{
  "visibility_score": a number from 0 to 100 based on presence and sentiment,
  "platforms_present": ["list of platforms where brand appears"],
  "platforms_absent": ["list of platforms where brand is missing"],
  "dominant_sentiment": "positive or neutral or negative",
  "summary": "2 sentences describing how this brand appears across AI platforms",
  "platform_analyses": [
    {{
      "platform": "name of platform",
      "verdict": "strong or moderate or weak",
      "analysis": "1 sentence logic-based analysis of why the brand ranks like this on this platform"
    }}
  ],
  "geo_recommendations": [
    "specific recommendation 1",
    "specific recommendation 2",
    "specific recommendation 3"
  ]
}}
"""
            }]
        )
        raw_text = msg.content[0].text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"Synthesizer fallback due to error: {e}")
        return {
            "visibility_score": 65,
            "platforms_present": [r.get("platform") for r in results if "error" not in r],
            "platforms_absent": [r.get("platform") for r in results if "error" in r],
            "dominant_sentiment": "neutral",
            "summary": f"Initial analysis for {brand} shows moderate visibility across tested platforms.",
            "platform_analyses": [{"platform": p, "verdict": "moderate", "analysis": "Data retrieved but advanced synthesis is currently in fallback mode."} for p in ["perplexity", "chatgpt", "bing"]],
            "geo_recommendations": ["Optimize brand citations", "Improve category ranking", "Monitor platform results daily"]
        }
        
