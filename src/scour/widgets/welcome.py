from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

LOGO = r"""
 ____
/ ___|  ___ ___  _   _ _ __
\___ \ / __/ _ \| | | | '__|
 ___) | (_| (_) | |_| | |
|____/ \___\___/ \__,_|_|
"""

HELP_TEXT = """[bold]Competitive research & inspiration finder[/bold]

[dim]Commands:[/dim]
  [cyan]/search "query"[/cyan]  — Search for competitors and inspiration
  [cyan]/history[/cyan]         — Browse past reports
  [cyan]/help[/cyan]            — Show this screen
  [cyan]/clear[/cyan]           — Return to this screen

[dim]Example:[/dim]
  [cyan]/search "best project management tools for developers"[/cyan]

[dim]Results are saved to[/dim] [yellow]./results/[/yellow]
"""


class WelcomeView(Widget):
    DEFAULT_CSS = """
    WelcomeView {
        align: center middle;
        padding: 2 4;
    }
    WelcomeView #logo {
        color: $accent;
        text-align: center;
        padding-bottom: 1;
    }
    WelcomeView #help {
        text-align: left;
        padding: 1 2;
        border: round $panel;
        width: auto;
        max-width: 70;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(LOGO, id="logo")
        yield Static(HELP_TEXT, id="help")
