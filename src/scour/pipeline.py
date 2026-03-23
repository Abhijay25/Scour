import re
from collections.abc import Callable

from scour.api import gemini, serper, tinyfish
from scour.models import FullReport, PipelineError, RankedResult
from scour.utils import save_report

_URL_PATTERN = re.compile(r'https?://\S+')


async def run_search(query: str, on_status: Callable[[str], None], *, top_n: int = 5) -> FullReport:
    # Extract URLs from query and build a cleaner search query
    urls_in_query = _URL_PATTERN.findall(query)
    search_query = _URL_PATTERN.sub('', query).strip()
    on_status("Searching the web...")
    results = await serper.search(search_query, num=15)

    on_status(f"Ranking {len(results)} results...")
    ranked = await gemini.rank_results(query, results, has_urls=bool(urls_in_query), top_n=top_n)
    ranked = ranked[:top_n]  # hard cap in case LLM returns more

    if not ranked and not urls_in_query:
        raise PipelineError("rank", "No relevant competitor sites found — try a more specific query or include a company URL")

    # Add any URLs from the original query as guaranteed extraction targets
    ranked_urls = {r.url for r in ranked}
    for url in urls_in_query:
        if url not in ranked_urls:
            ranked.append(RankedResult(url=url, title=url, relevance_reason="Provided in query"))

    urls = [r.url for r in ranked]
    total = len(urls)
    extracted_count = 0

    def _on_url_status(url: str, success: bool) -> None:
        nonlocal extracted_count
        extracted_count += 1
        on_status(f"Extracted {extracted_count}/{total} sites...")

    on_status(f"Extracting content from {total} sites...")
    extracted = await tinyfish.extract_urls(urls, query, on_url_status=_on_url_status)

    successful = sum(1 for e in extracted if e.success)
    on_status(f"Analyzing {successful} pages with Gemini...")
    report = await gemini.analyze_content(query, extracted)

    on_status("Saving report...")
    path = save_report(query, report.markdown)
    report.saved_path = path

    return report
