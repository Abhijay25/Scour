from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.widget import Widget
from textual.widgets import Static

LOGO = r""" ____
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
  [cyan]/quit[/cyan]            — Exit Scour

[dim]Example:[/dim]
  [cyan]/search "best project management tools for developers"[/cyan]

[dim]Results are saved to[/dim] [yellow]~/.local/share/scour/results/[/yellow]
"""


class WelcomeView(Widget):
    DEFAULT_CSS = """
    WelcomeView {
        width: 100%;
        height: 100%;
    }
    WelcomeView Middle {
        width: 100%;
        height: 100%;
    }
    WelcomeView Vertical {
        width: auto;
        height: auto;
    }
    WelcomeView #logo {
        color: $accent;
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }
    WelcomeView #help {
        text-align: left;
        padding: 1 2;
        border: round $panel;
        width: 70;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Vertical():
                with Center():
                    yield Static(LOGO, id="logo")
                with Center():
                    yield Static(HELP_TEXT, id="help")
