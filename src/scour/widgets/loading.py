from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, LoadingIndicator


class LoadingView(Widget):
    DEFAULT_CSS = """
    LoadingView {
        align: center middle;
    }
    LoadingView LoadingIndicator {
        height: 3;
    }
    LoadingView #status {
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Label("", id="status")

    def set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)
