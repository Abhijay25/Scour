import httpx

from scour.models import PipelineError, SearchResult
from scour.utils import get_env

SERPER_URL = "https://google.serper.dev/search"


async def search(query: str, num: int = 10) -> list[SearchResult]:
    try:
        api_key = get_env("SERPER_API_KEY")
    except RuntimeError as e:
        raise PipelineError("search", str(e))

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                SERPER_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status in (401, 403):
            raise PipelineError("search", f"Serper API key invalid or unauthorized (HTTP {status}) — check SERPER_API_KEY in ~/.config/scour/.env")
        if status == 429:
            raise PipelineError("search", "Serper rate limit exceeded — check your plan at serper.dev")
        raise PipelineError("search", f"Serper HTTP {status}: {e.response.text[:200]}")
    except httpx.RequestError as e:
        raise PipelineError("search", f"Request failed: {e}")

    organic = data.get("organic", [])
    if not organic:
        raise PipelineError("search", "No results returned from Serper")

    return [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
        )
        for item in organic
        if item.get("link")
    ]
