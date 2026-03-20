import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing environment variable: {key}")
    return val


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:60]


def results_dir() -> Path:
    path = Path("results")
    path.mkdir(exist_ok=True)
    return path


def save_report(query: str, markdown: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(query)
    filename = f"{date_str}-{slug}.md"
    path = results_dir() / filename
    path.write_text(markdown, encoding="utf-8")
    return str(path)


def list_reports() -> list[Path]:
    return sorted(results_dir().glob("*.md"), reverse=True)
