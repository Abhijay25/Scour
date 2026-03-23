from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

LOGO = r""" ____
/ ___|  ___ ___  _   _ _ __
\___ \ / __/ _ \| | | | '__|
 ___) | (_| (_) | |_| | |
|____/ \___\___/ \__,_|_|
"""

WELCOME_TEXT = (
    "[bold]Competitive research & inspiration finder[/bold]\n"
    "\n"
    "[dim]Get started:[/dim]\n"
    "  [cyan]/search[/cyan] [yellow]<query>[/yellow]    — research a market or find competitors\n"
    "  [cyan]/help[/cyan]               — show all commands and tips\n"
    "  [cyan]/quit[/cyan]               — exit Scour\n"
    "\n"
    "[dim]Example:[/dim]\n"
    "  [cyan]/search SaaS tools for AI-assisted grading for teachers[/cyan]\n"
)

HELP_TEXT = (
    "[bold]Commands[/bold]\n"
    "\n"
    "  [cyan]/search[/cyan] [yellow]<query>[/yellow]\n"
    "    Search the web, extract content from the top results, and generate a competitive analysis.\n"
    "    Quotes are optional — just type naturally. The analysis adapts to your intent:\n"
    "    ask about UX and get UX insights, ask about pricing and get pricing comparisons.\n"
    "    You can include URLs: [cyan]/search stem cells similar to https://example.com[/cyan]\n"
    "\n"
    "  [cyan]/history[/cyan]\n"
    "    Browse all past reports saved on your machine. Select one to read it.\n"
    "    Reports are stored at [yellow]~/.local/share/scour/results/[/yellow]\n"
    "\n"
    "  [cyan]/copy[/cyan]\n"
    "    Copy the current report's markdown to your clipboard.\n"
    "\n"
    "  [cyan]/open[/cyan]\n"
    "    Open the reports folder in your file manager.\n"
    "\n"
    "  [cyan]/rerun[/cyan]\n"
    "    Re-run the search for the currently previewed report.\n"
    "\n"
    "  [cyan]/delete[/cyan]\n"
    "    Delete the selected report in history view.\n"
    "\n"
    "  [cyan]/clear[/cyan]\n"
    "    Return to the home screen.\n"
    "\n"
    "  [cyan]/help[/cyan]\n"
    "    Show this screen.\n"
    "\n"
    "  [cyan]/quit[/cyan]  [dim]or[/dim]  [cyan]/exit[/cyan]\n"
    "    Exit Scour.\n"
    "\n"
    "[bold]Keyboard shortcuts[/bold]\n"
    "\n"
    "  [cyan]Up / Down[/cyan]    Cycle through previous commands\n"
    "  [cyan]Escape[/cyan]       Go back to the previous screen\n"
    "  [cyan]d[/cyan]            Delete selected report (in history view)\n"
    "\n"
    "[bold]Examples[/bold]\n"
    "\n"
    "  [cyan]/search best project management tools for developers[/cyan]\n"
    "  [cyan]/search competitor analysis for CRM platforms[/cyan]\n"
    "  [cyan]/search UX patterns in B2B SaaS onboarding flows[/cyan]\n"
)


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
    WelcomeView #welcome {
        text-align: left;
        padding: 1 3;
        border: round $panel;
        width: 80;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Vertical():
                with Center():
                    yield Static(LOGO, id="logo")
                with Center():
                    yield Static(WELCOME_TEXT, id="welcome")


class HelpView(Widget):
    DEFAULT_CSS = """
    HelpView {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    HelpView VerticalScroll {
        width: 96;
        height: 100%;
        border: round $panel;
        padding: 1 3;
    }
    HelpView #help {
        text-align: left;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(HELP_TEXT, id="help")
