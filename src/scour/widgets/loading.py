import time

from textual.app import ComposeResult
from textual.timer import Timer
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
        width: 100%;
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }
    LoadingView #elapsed {
        width: 100%;
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._start_time: float = 0
        self._timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Label("", id="status")
        yield Label("", id="elapsed")

    def set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)

    def start_timer(self) -> None:
        self._start_time = time.monotonic()
        self._update_elapsed()
        self._timer = self.set_interval(1.0, self._update_elapsed)

    def stop_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.query_one("#elapsed", Label).update("")

    def _update_elapsed(self) -> None:
        elapsed = int(time.monotonic() - self._start_time)
        if elapsed < 60:
            text = f"{elapsed}s elapsed"
        else:
            text = f"{elapsed // 60}m {elapsed % 60}s elapsed"
        self.query_one("#elapsed", Label).update(text)
