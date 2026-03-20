from collections.abc import Callable

from scour.api import gemini, serper, tinyfish
from scour.models import FullReport, PipelineError
from scour.utils import save_report


async def run_search(query: str, on_status: Callable[[str], None]) -> FullReport:
    on_status("Searching the web...")
    results = await serper.search(query)

    on_status(f"Ranking {len(results)} results...")
    ranked = await gemini.rank_results(query, results)

    urls = [r.url for r in ranked]
    on_status(f"Extracting content from {len(urls)} sites...")
    extracted = await tinyfish.extract_urls(urls, query)

    successful = sum(1 for e in extracted if e.success)
    on_status(f"Analyzing {successful} pages with Gemini...")
    report = await gemini.analyze_content(query, extracted)

    on_status("Saving report...")
    path = save_report(query, report.markdown)
    report.saved_path = path

    return report
