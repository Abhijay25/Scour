import re
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, Markdown


class ReportPreview(Widget):
    DEFAULT_CSS = """
    ReportPreview {
        height: 1fr;
        width: 100%;
        layout: vertical;
    }
    ReportPreview #preview-hint {
        color: $text-muted;
        text-style: italic;
        padding: 0 2 1 2;
        border-bottom: solid $panel;
        height: auto;
    }
    ReportPreview Markdown {
        height: 1fr;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_query: str = ""

    def compose(self) -> ComposeResult:
        yield Label("Escape to go back  |  /rerun to search again", id="preview-hint")
        yield Markdown("", id="markdown-content")

    def show_report(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            content = f"# Error\n\nCould not read file: {e}"
        # Parse query from markdown heading
        match = re.search(r'^# Competitive Analysis:\s*(.+)', content, re.MULTILINE)
        self.current_query = match.group(1).strip() if match else ""
        self.query_one("#markdown-content", Markdown).update(content)
