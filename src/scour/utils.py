import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "scour"
ENV_FILE = CONFIG_DIR / ".env"
RESULTS_DIR = Path.home() / ".local" / "share" / "scour" / "results"

load_dotenv(ENV_FILE)


def get_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing environment variable: {key} — edit {ENV_FILE}")
    return val


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:60]


def results_dir() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def save_report(query: str, markdown: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d-%H%M")
    slug = slugify(query)
    filename = f"{date_str}-{slug}.md"
    path = results_dir() / filename
    path.write_text(markdown, encoding="utf-8")
    return str(path)


def list_reports() -> list[Path]:
    return sorted(results_dir().glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def parse_report_meta(path: Path) -> tuple[str, str]:
    """Extract (date_label, query) from a report file."""
    # Date from filename: 2026-03-20-1758-slug.md -> 2026-03-20
    name = path.stem
    date_label = name[:10] if len(name) >= 10 else ""
    # Query from first heading line
    query = ""
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# Competitive Analysis:"):
                    query = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass
    return date_label, query
