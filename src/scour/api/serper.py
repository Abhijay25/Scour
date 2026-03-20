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
        raise PipelineError("search", f"HTTP {e.response.status_code}: {e.response.text}")
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
