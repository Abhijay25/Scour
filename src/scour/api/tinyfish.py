import asyncio
import json
from collections.abc import Callable

import httpx

from scour.models import ExtractedContent, PipelineError
from scour.utils import get_env

TINYFISH_URL = "https://agent.tinyfish.ai/v1/automation/run-sse"
SEMAPHORE_LIMIT = 3
TIMEOUT = 60


async def _extract_one(
    client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str, goal: str,
    on_url_status: "Callable | None" = None,
) -> ExtractedContent:
    async with sem:
        try:
            async with client.stream(
                "POST",
                TINYFISH_URL,
                json={"url": url, "goal": goal},
                timeout=TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                result = None
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "COMPLETE":
                        result = event.get("result", "")
                        break

            if result is None:
                content = ExtractedContent(
                    url=url, title="", text="", success=False, error="No COMPLETE event received"
                )
            elif not isinstance(result, str):
                content = ExtractedContent(url=url, title="", text=json.dumps(result), success=True)
            else:
                content = ExtractedContent(url=url, title="", text=result, success=True)
            if on_url_status:
                on_url_status(url, content.success)
            return content
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403):
                content = ExtractedContent(url=url, title="", text="", success=False, error=f"Tinyfish API key invalid (HTTP {status})")
            elif status == 429:
                content = ExtractedContent(url=url, title="", text="", success=False, error="Tinyfish rate limit exceeded")
            else:
                content = ExtractedContent(url=url, title="", text="", success=False, error=f"HTTP {status}")
            if on_url_status:
                on_url_status(url, False)
            return content
        except Exception as e:
            if on_url_status:
                on_url_status(url, False)
            err = str(e) or f"{type(e).__name__} (no details)"
            return ExtractedContent(url=url, title="", text="", success=False, error=err)


async def extract_urls(
    urls: list[str], query: str, on_url_status: Callable | None = None,
) -> list[ExtractedContent]:
    try:
        api_key = get_env("TINYFISH_API_KEY")
    except RuntimeError as e:
        raise PipelineError("extract", str(e))

    goal = (
        "Extract all relevant information from this page. "
        "Include key details, descriptions, features, and any structured data. "
        f"The user is researching: {query}"
    )

    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    async with httpx.AsyncClient(
        headers={"X-API-Key": api_key},
        timeout=TIMEOUT,
    ) as client:
        tasks = [_extract_one(client, sem, url, goal, on_url_status) for url in urls]
        return await asyncio.gather(*tasks)
