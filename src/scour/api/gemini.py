import asyncio
import json

import httpx

from scour.models import (
    CompetitiveEdge,
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


def _build_markdown(query: str, analyses: list[CompetitorAnalysis], edge: CompetitiveEdge | None = None) -> str:
    lines = [f"# Competitive Analysis: {query}\n"]

    if edge:
        lines.append("## Competitive Edge\n")
        if edge.ideas_to_steal:
            lines.append("### ✅ Ideas to Steal")
            for idea in edge.ideas_to_steal:
                lines.append(f"- {idea}")
            lines.append("")
        if edge.pitfalls_to_avoid:
            lines.append("### ❌ Pitfalls to Avoid")
            for p in edge.pitfalls_to_avoid:
                lines.append(f"- {p}")
            lines.append("")
        if edge.gaps:
            lines.append("### Market Gaps")
            for g in edge.gaps:
                lines.append(f"- {g}")
            lines.append("")

    lines.append("---\n")

    for a in analyses:
        lines.append(f"## {a.title}\n")
        lines.append(f"**URL:** {a.url}\n")
        if a.summary:
            lines.append(f"{a.summary}\n")
        if a.strengths:
            lines.append("**✅ Strengths:**")
            for s in a.strengths:
                lines.append(f"- {s}")
            lines.append("")
        if a.weaknesses:
            lines.append("**❌ Weaknesses:**")
            for w in a.weaknesses:
                lines.append(f"- {w}")
            lines.append("")
    return "\n".join(lines)


async def _call_gemini(api_key: str, prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    GEMINI_URL,
                    params={"key": api_key},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            break
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
            last_error = PipelineError("gemini", f"HTTP {status}: {msg}")
            if status >= 500 and attempt == 0:
                await asyncio.sleep(2)
                continue
            raise last_error
        except httpx.RequestError as e:
            last_error = PipelineError("gemini", f"Request failed: {e}")
            if attempt == 0:
                await asyncio.sleep(2)
                continue
            raise last_error
    else:
        raise last_error  # type: ignore[misc]

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise PipelineError("gemini", f"Unexpected response structure: {e}")


async def rank_results(query: str, results: list[SearchResult], *, has_urls: bool = False) -> list[RankedResult]:
    try:
        api_key = get_env("GEMINI_API_KEY")
    except RuntimeError as e:
        raise PipelineError("rank", str(e))

    results_text = "\n".join(
        f"{i+1}. Title: {r.title}\n   URL: {r.url}\n   Snippet: {r.snippet}"
        for i, r in enumerate(results)
    )

    business_hint = (
        "\nIMPORTANT: The user provided a specific company/product URL, so this is clearly business-focused competitive research. "
        "Only return companies, startups, products, or services that compete in the same market. "
        "Do NOT include academic papers, research studies, journal articles, clinical trials, or educational resources — these are never useful for competitive analysis.\n"
        if has_urls else ""
    )

    prompt = f"""You are helping with competitive research for: "{query}"

This tool is for BUSINESS competitive analysis — finding companies, startups, products, and services in a market. It is NOT for academic or scientific research.

Prioritize early-stage startups, small companies, and indie products — these are the most relevant competitors for someone using this tool. Large enterprises are fine to include but should not crowd out smaller players.
{business_hint}
Here are search results:
{results_text}

Pick the 3-5 results most useful for competitive research. Strongly prefer direct startup/company/product pages. For each, explain why it's relevant as a business competitor.

Exclude: academic journals, PubMed/NIH studies, Wikipedia, research papers, clinical trials, and news articles unless they profile a specific company.

If fewer than 3 strong matches exist, include the best available — never return fewer than 2 results.

Return JSON in this exact format:
{{
  "ranked": [
    {{
      "url": "https://...",
      "title": "...",
      "relevance_reason": "brief explanation of why this is relevant"
    }}
  ]
}}"""

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

    prompt = f"""You are a strategic competitive analyst helping a startup founder understand their market for: "{query}"

Analyze each competitor below from a BUSINESS STRATEGY perspective — not as a product reviewer. Frame your analysis for someone building a startup that will compete in this space.

For each competitor, focus on:
- Business model: how they make money, pricing structure, revenue levers (e.g. seat-based, usage-based, freemium-to-enterprise)
- Market positioning: who they target, how they differentiate, what pain point they own
- Stage & traction: are they a scrappy startup, growth-stage, or established? Funding, user counts, notable clients, G2/Capterra/Product Hunt ratings — surface anything mentioned on the page
- Product/UX strategy: specific design decisions and their business rationale (not "clean UI" — instead "uses progressive onboarding to reduce time-to-value for non-technical buyers")
- Strategic vulnerabilities: gaps a new startup could exploit

AVOID generic observations like "easy to use", "good support", "nice design".
INSTEAD be specific: "charges per-seat which creates friction for solo founders but drives natural expansion revenue in teams"

After analyzing individual competitors, produce a "competitive_edge" section that synthesizes insights ACROSS ALL competitors:
- ideas_to_steal: the 3-5 most valuable strategic moves worth adopting (specific and actionable)
- pitfalls_to_avoid: the 3-5 patterns that are clearly hurting competitors or limiting their growth
- gaps: 2-3 unmet needs or market positions that none of them address well — opportunities for a new startup to own

{pages_text}

Return JSON in this exact format:
{{
  "analyses": [
    {{
      "url": "https://...",
      "title": "Site Name",
      "summary": "2-3 sentence business-focused overview including any traction signals",
      "strengths": ["specific strategic strength 1", "specific strategic strength 2"],
      "weaknesses": ["specific strategic weakness 1", "specific strategic weakness 2"]
    }}
  ],
  "competitive_edge": {{
    "ideas_to_steal": ["actionable idea 1", "actionable idea 2"],
    "pitfalls_to_avoid": ["specific pitfall 1", "specific pitfall 2"],
    "gaps": ["market gap 1", "market gap 2"]
  }}
}}"""

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
        edge_data = data.get("competitive_edge", {})
        edge = CompetitiveEdge(
            ideas_to_steal=edge_data.get("ideas_to_steal", []),
            pitfalls_to_avoid=edge_data.get("pitfalls_to_avoid", []),
            gaps=edge_data.get("gaps", []),
        )
        markdown = _build_markdown(query, analyses, edge)
        return FullReport(query=query, analyses=analyses, edge=edge, markdown=markdown)
    except (json.JSONDecodeError, KeyError) as e:
        raise PipelineError("analyze", f"Failed to parse Gemini response: {e}")
