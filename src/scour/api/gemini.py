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

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
MAX_WORDS_PER_PAGE = 5000


def _truncate(text: str, max_words: int = MAX_WORDS_PER_PAGE) -> str:
    words = text.split()
    return " ".join(words[:max_words])


def _build_markdown(query: str, analyses: list[CompetitorAnalysis]) -> str:
    lines = [f"# Competitive Analysis: {query}\n"]
    for a in analyses:
        lines.append(f"## {a.title}\n")
        lines.append(f"**URL:** {a.url}\n")
        if a.summary:
            lines.append(f"{a.summary}\n")
        if a.strengths:
            lines.append("**Strengths:**")
            for s in a.strengths:
                lines.append(f"- {s}")
            lines.append("")
        if a.weaknesses:
            lines.append("**Weaknesses:**")
            for w in a.weaknesses:
                lines.append(f"- {w}")
            lines.append("")
    return "\n".join(lines)


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
        status = e.response.status_code
        try:
            msg = e.response.json().get("error", {}).get("message", "").split("\n")[0]
        except Exception:
            msg = e.response.text[:200]
        if status in (401, 403):
            raise PipelineError("gemini", f"Gemini API key invalid or unauthorized (HTTP {status}) — check GEMINI_API_KEY in ~/.config/scour/.env")
        if status == 429:
            raise PipelineError("gemini", "Gemini quota exhausted — free-tier limit reached. Wait or enable billing at aistudio.google.com.")
        raise PipelineError("gemini", f"HTTP {status}: {msg}")
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

    prompt = f"""You are helping with competitive research for: "{query}"

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
        errors = list({e.error for e in extracted if e.error})
        detail = "; ".join(errors[:3]) if errors else "unknown error"
        raise PipelineError("extract", f"No content could be extracted — {detail}")

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
  ]
}}

Be specific and actionable. Always consider target audience and unique value propositions. Beyond that, determine what other aspects are most relevant based on the user's research query — adapt your analysis to their intent."""

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
        markdown = _build_markdown(query, analyses)
        return FullReport(query=query, analyses=analyses, markdown=markdown)
    except (json.JSONDecodeError, KeyError) as e:
        raise PipelineError("analyze", f"Failed to parse Gemini response: {e}")
