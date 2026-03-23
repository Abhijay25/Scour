from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from scour.models import CompetitiveEdge, FullReport


class BottomLineBlock(Widget):
    DEFAULT_CSS = """
    BottomLineBlock {
        border: round $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
        width: 100%;
    }
    """

    def __init__(self, bottom_line: str, positioning: str, **kwargs):
        super().__init__(**kwargs)
        self.bottom_line = bottom_line
        self.positioning = positioning

    def compose(self) -> ComposeResult:
        lines = ["[bold $accent]Bottom Line[/bold $accent]\n"]
        lines.append(self.bottom_line)
        if self.positioning:
            lines.append(f"\n[italic]{self.positioning}[/italic]")
        yield Static("\n".join(lines), markup=True)


class CompetitiveEdgeBlock(Widget):
    DEFAULT_CSS = """
    CompetitiveEdgeBlock {
        border: round $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
        width: 100%;
    }
    """

    def __init__(self, edge: CompetitiveEdge, **kwargs):
        super().__init__(**kwargs)
        self.edge = edge

    def compose(self) -> ComposeResult:
        e = self.edge
        lines = ["[bold $accent]Competitive Edge[/bold $accent]"]
        if e.ideas_to_steal:
            lines.append("\n[bold green]✅  Ideas to steal[/bold green]")
            for idea in e.ideas_to_steal:
                lines.append(f"  [green]+[/green] {idea}")
        if e.pitfalls_to_avoid:
            lines.append("\n[bold red]❌  Pitfalls to avoid[/bold red]")
            for p in e.pitfalls_to_avoid:
                lines.append(f"  [red]-[/red] {p}")
        if e.gaps:
            lines.append("\n[bold yellow]  Market gaps[/bold yellow]")
            for g in e.gaps:
                lines.append(f"  [yellow]→[/yellow] {g}")
        yield Static("\n".join(lines), markup=True)


class CompetitorBlock(Widget):
    DEFAULT_CSS = """
    CompetitorBlock {
        border: round $panel;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
        width: 100%;
    }
    """

    def __init__(self, analysis, **kwargs):
        super().__init__(**kwargs)
        self.analysis = analysis

    def compose(self) -> ComposeResult:
        a = self.analysis
        lines = [
            f"[bold $accent]{a.title}[/bold $accent]",
            f"[italic dim]{a.url}[/italic dim]",
            f"\n{a.summary}",
        ]
        if a.strengths:
            lines.append("\n[bold green]Strengths[/bold green]")
            for s in a.strengths:
                lines.append(f"  [green]+[/green] {s}")
        if a.weaknesses:
            lines.append("\n[bold red]Weaknesses[/bold red]")
            for w in a.weaknesses:
                lines.append(f"  [red]-[/red] {w}")
        yield Static("\n".join(lines), markup=True)


class ResultsView(Widget):
    DEFAULT_CSS = """
    ResultsView {
        height: 1fr;
        width: 100%;
    }
    ResultsView #results-header {
        text-style: bold;
        color: $accent;
        padding: 1 2;
        width: 100%;
        border-bottom: solid $panel;
    }
    ResultsView VerticalScroll {
        height: 1fr;
        padding: 0 2 1 2;
    }
    ResultsView #saved-path {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._report: FullReport | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="results-header")
        with VerticalScroll(id="results-scroll"):
            yield Static("", id="saved-path")

    def show_report(self, report: FullReport) -> None:
        self._report = report
        self.query_one("#results-header", Static).update(
            f'Analysis: "{report.query}"  —  {len(report.analyses)} competitors'
        )
        scroll = self.query_one("#results-scroll", VerticalScroll)
        for block in scroll.query(CompetitorBlock):
            block.remove()
        for block in scroll.query(CompetitiveEdgeBlock):
            block.remove()
        for block in scroll.query(BottomLineBlock):
            block.remove()
        for block in scroll.query(".dig-deeper"):
            block.remove()
        for block in scroll.query(".niche-easter-egg"):
            block.remove()
        saved = scroll.query_one("#saved-path", Static)
        if report.bottom_line:
            scroll.mount(BottomLineBlock(report.bottom_line, report.positioning), before=saved)
        if report.edge:
            scroll.mount(CompetitiveEdgeBlock(report.edge), before=saved)
        for analysis in report.analyses:
            scroll.mount(CompetitorBlock(analysis), before=saved)
        if len(report.analyses) <= 2:
            niche_msg = Static(
                "[italic dim]Looks like you're in a niche market — the field is wide open. Take control![/italic dim]",
                markup=True,
                classes="niche-easter-egg",
            )
            niche_msg.styles.padding = (1, 2)
            niche_msg.styles.margin = (0, 0, 1, 0)
            niche_msg.styles.width = "100%"
            scroll.mount(niche_msg, before=saved)
        if report.suggested_queries:
            lines = ["[bold $accent]Dig Deeper[/bold $accent]\n"]
            for sq in report.suggested_queries:
                lines.append(f"  [cyan]/search {sq}[/cyan]")
            dig_deeper = Static("\n".join(lines), markup=True, classes="dig-deeper")
            dig_deeper.styles.border = ("round", "$panel")
            dig_deeper.styles.padding = (1, 2)
            dig_deeper.styles.margin = (0, 0, 1, 0)
            dig_deeper.styles.width = "100%"
            scroll.mount(dig_deeper, before=saved)
        if report.saved_path:
            saved.update(f"Report saved to {report.saved_path}")
