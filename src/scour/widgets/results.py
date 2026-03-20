from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from scour.models import FullReport


class CompetitorBlock(Widget):
    DEFAULT_CSS = """
    CompetitorBlock {
        border: round $panel;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    CompetitorBlock .title {
        color: $accent;
        text-style: bold;
    }
    CompetitorBlock .url {
        color: $text-muted;
        text-style: italic;
    }
    CompetitorBlock .summary {
        padding: 1 0;
    }
    CompetitorBlock .section-header {
        text-style: bold;
        color: $success;
    }
    CompetitorBlock .weakness-header {
        text-style: bold;
        color: $error;
    }
    CompetitorBlock .bullet {
        padding-left: 2;
        color: $text;
    }
    """

    def __init__(self, analysis, **kwargs):
        super().__init__(**kwargs)
        self.analysis = analysis

    def compose(self) -> ComposeResult:
        a = self.analysis
        yield Label(a.title, classes="title")
        yield Label(a.url, classes="url")
        yield Label(a.summary, classes="summary")

        if a.strengths:
            yield Label("Strengths", classes="section-header")
            for s in a.strengths:
                yield Label(f"+ {s}", classes="bullet")

        if a.weaknesses:
            yield Label("Weaknesses", classes="weakness-header")
            for w in a.weaknesses:
                yield Label(f"- {w}", classes="bullet")


class ResultsView(Widget):
    DEFAULT_CSS = """
    ResultsView {
        padding: 1 2;
        overflow-y: auto;
        height: 1fr;
    }
    ResultsView #results-header {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
        border-bottom: solid $panel;
        margin-bottom: 1;
    }
    ResultsView #saved-path {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._report: FullReport | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="results-header")
        yield Label("", id="saved-path")

    def show_report(self, report: FullReport) -> None:
        self._report = report
        self.query_one("#results-header", Label).update(
            f'Analysis: "{report.query}" — {len(report.analyses)} sites'
        )
        # Remove any existing competitor blocks
        for block in self.query(CompetitorBlock):
            block.remove()
        # Mount new blocks before the saved-path label
        saved_label = self.query_one("#saved-path", Label)
        for analysis in report.analyses:
            self.mount(CompetitorBlock(analysis), before=saved_label)
        if report.saved_path:
            saved_label.update(f"Saved to: {report.saved_path}")
