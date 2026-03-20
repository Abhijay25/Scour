import asyncio

import httpx

from scour.models import ExtractedContent, PipelineError
from scour.utils import get_env

TINYFISH_URL = "https://r.jina.ai/"
SEMAPHORE_LIMIT = 3
TIMEOUT = 30


async def _extract_one(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> ExtractedContent:
    async with sem:
        try:
            resp = await client.get(
                TINYFISH_URL + url,
                headers={"Accept": "application/json"},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return ExtractedContent(
                url=url,
                title=data.get("data", {}).get("title", ""),
                text=data.get("data", {}).get("content", ""),
                success=True,
            )
        except Exception as e:
            return ExtractedContent(url=url, title="", text="", success=False, error=str(e))


async def extract_urls(urls: list[str]) -> list[ExtractedContent]:
    try:
        api_key = get_env("TINYFISH_API_KEY")
    except RuntimeError as e:
        raise PipelineError("extract", str(e))

    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TIMEOUT,
    ) as client:
        tasks = [_extract_one(client, sem, url) for url in urls]
        return await asyncio.gather(*tasks)
