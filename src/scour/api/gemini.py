import json

import httpx

from scour.models import (
    CompetitorAnalysis,
    ExtractedContent,
    FullReport,
    PipelineError,
    RankedResult,
    SearchResult,
)
from scour.utils import get_env

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
MAX_WORDS_PER_PAGE = 5000


def _truncate(text: str, max_words: int = MAX_WORDS_PER_PAGE) -> str:
    words = text.split()
    return " ".join(words[:max_words])


async def _call_gemini(api_key: str, prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                GEMINI_URL,
                params={"key": api_key},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise PipelineError("gemini", f"HTTP {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise PipelineError("gemini", f"Request failed: {e}")

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise PipelineError("gemini", f"Unexpected response structure: {e}")


async def rank_results(query: str, results: list[SearchResult]) -> list[RankedResult]:
    try:
        api_key = get_env("GEMINI_API_KEY")
    except RuntimeError as e:
        raise PipelineError("rank", str(e))

    results_text = "\n".join(
        f"{i+1}. Title: {r.title}\n   URL: {r.url}\n   Snippet: {r.snippet}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are helping a developer find inspiration and competitive analysis for: "{query}"

Here are search results:
{results_text}

Pick the 3-5 most relevant results for competitive analysis. Return JSON in this exact format:
{{
  "ranked": [
    {{
      "url": "https://...",
      "title": "...",
      "relevance_reason": "brief explanation of why this is relevant"
    }}
  ]
}}

Only include results that are actual products/tools/services (not documentation, blog posts, or news articles unless directly relevant). Prefer products with public-facing websites."""

    raw = await _call_gemini(api_key, prompt)

    try:
        data = json.loads(raw)
        return [
            RankedResult(
                url=item["url"],
                title=item["title"],
                relevance_reason=item.get("relevance_reason", ""),
            )
            for item in data.get("ranked", [])
        ]
    except (json.JSONDecodeError, KeyError):
        # Fallback: return top 5 raw results as RankedResult
        return [
            RankedResult(url=r.url, title=r.title, relevance_reason=r.snippet)
            for r in results[:5]
        ]


async def analyze_content(query: str, extracted: list[ExtractedContent]) -> FullReport:
    try:
        api_key = get_env("GEMINI_API_KEY")
    except RuntimeError as e:
        raise PipelineError("analyze", str(e))

    successful = [e for e in extracted if e.success and e.text]
    if not successful:
        raise PipelineError("analyze", "No content could be extracted from any URL")

    pages_text = ""
    for i, page in enumerate(successful):
        truncated = _truncate(page.text)
        pages_text += f"\n\n--- Page {i+1}: {page.title} ({page.url}) ---\n{truncated}"

    prompt = f"""You are a competitive analysis expert. The user is researching: "{query}"

Analyze each of the following competitor/inspiration sites and identify their strengths and weaknesses.

{pages_text}

Return JSON in this exact format:
{{
  "analyses": [
    {{
      "url": "https://...",
      "title": "Site Name",
      "strengths": ["strength 1", "strength 2", "strength 3"],
      "weaknesses": ["weakness 1", "weakness 2"],
      "summary": "2-3 sentence overview of this tool/site"
    }}
  ],
  "markdown": "# Competitive Analysis: {query}\\n\\n[full markdown report with sections for each site, including strengths, weaknesses, and a final comparison table]"
}}

Be specific and actionable. Focus on features, UX, pricing model, target audience, and unique value propositions."""

    raw = await _call_gemini(api_key, prompt)

    try:
        data = json.loads(raw)
        analyses = [
            CompetitorAnalysis(
                url=item["url"],
                title=item["title"],
                strengths=item.get("strengths", []),
                weaknesses=item.get("weaknesses", []),
                summary=item.get("summary", ""),
            )
            for item in data.get("analyses", [])
        ]
        markdown = data.get("markdown", "")
        return FullReport(query=query, analyses=analyses, markdown=markdown)
    except (json.JSONDecodeError, KeyError) as e:
        raise PipelineError("analyze", f"Failed to parse Gemini response: {e}")
