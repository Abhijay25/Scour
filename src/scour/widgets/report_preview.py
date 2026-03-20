from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Markdown


class ReportPreview(Widget):
    DEFAULT_CSS = """
    ReportPreview {
        padding: 1 2;
        overflow-y: auto;
    }
    ReportPreview #preview-hint {
        color: $text-muted;
        text-style: italic;
        padding-bottom: 1;
        border-bottom: solid $panel;
        margin-bottom: 1;
    }
    ReportPreview Markdown {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Press Escape to go back", id="preview-hint")
        yield Markdown("", id="markdown-content")

    def show_report(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            content = f"# Error\n\nCould not read file: {e}"
        self.query_one("#markdown-content", Markdown).update(content)
