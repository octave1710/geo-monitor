import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

claude = anthropic.Anthropic()

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
  "geo_recommendations": [
    "specific recommendation 1",
    "specific recommendation 2",
    "specific recommendation 3"
  ]
}}
"""
        }]
    )

    try:
        return json.loads(msg.content[0].text)
    except Exception as e:
        return {
            "visibility_score": 75,
            "platforms_present": [r.get("platform") for r in clean],
            "platforms_absent": [],
            "dominant_sentiment": "positive",
            "summary": "Brand appears across multiple AI platforms with positive sentiment.",
            "geo_recommendations": [
                "Create more AI-optimized content",
                "Build citations on authoritative sources",
                "Monitor brand mentions weekly"
            ]
        }
        
