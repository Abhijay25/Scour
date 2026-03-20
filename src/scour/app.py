from textual.app import App, ComposeResult
from textual.widgets import ContentSwitcher, Input

from scour.models import PipelineError
from scour.pipeline import run_search
from scour.widgets.history import HistoryView, ReportSelected
from scour.widgets.loading import LoadingView
from scour.widgets.report_preview import ReportPreview
from scour.widgets.results import ResultsView
from scour.widgets.welcome import WelcomeView


class ScourApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-rows: 1fr auto;
    }

    ContentSwitcher {
        height: 1fr;
    }

    Input#command-bar {
        dock: bottom;
        height: 3;
        border: tall $accent;
    }

    Input#command-bar:focus {
        border: tall $accent;
    }
    """

    TITLE = "Scour"
    SUB_TITLE = "Competitive research & inspiration finder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._previous_view: str = "welcome"

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="welcome", id="main-content"):
            yield WelcomeView(id="welcome")
            yield LoadingView(id="loading")
            yield ResultsView(id="results")
            yield HistoryView(id="history")
            yield ReportPreview(id="preview")
        yield Input(placeholder='/search "query" | /history | /help | /clear', id="command-bar")

    def on_mount(self) -> None:
        self.query_one("#command-bar", Input).focus()

    def _switch_to(self, view_id: str) -> None:
        current = self.query_one("#main-content", ContentSwitcher).current
        if current != view_id:
            self._previous_view = current
        self.query_one("#main-content", ContentSwitcher).current = view_id

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        event.input.clear()
        if not raw:
            return

        if raw.startswith("/search "):
            query = raw[8:].strip().strip('"').strip("'")
            if query:
                self._do_search(query)
            else:
                self.notify('Usage: /search "your query"', severity="warning")

        elif raw == "/history":
            self._switch_to("history")
            self.query_one(HistoryView).refresh_list()

        elif raw == "/help":
            self._switch_to("welcome")

        elif raw == "/clear":
            self._switch_to("welcome")

        else:
            self.notify(f"Unknown command: {raw}", severity="warning")

    def on_key(self, event) -> None:
        if event.key == "escape":
            current = self.query_one("#main-content", ContentSwitcher).current
            if current in ("preview", "history"):
                self._switch_to(self._previous_view if self._previous_view != current else "welcome")
            self.query_one("#command-bar", Input).focus()

    def on_report_selected(self, event: ReportSelected) -> None:
        self._switch_to("preview")
        self.query_one(ReportPreview).show_report(event.path)

    def _do_search(self, query: str) -> None:
        async def _search_worker() -> None:
            loading = self.query_one(LoadingView)
            self._switch_to("loading")
            loading.set_status("Starting search...")

            def on_status(msg: str) -> None:
                loading.set_status(msg)

            try:
                report = await run_search(query, on_status)
                results_view = self.query_one(ResultsView)
                results_view.show_report(report)
                self._switch_to("results")
                self.notify(f"Report saved to {report.saved_path}", severity="information")
            except PipelineError as e:
                self._switch_to("welcome")
                self.notify(str(e), severity="error", timeout=8)
            except Exception as e:
                self._switch_to("welcome")
                self.notify(f"Unexpected error: {e}", severity="error", timeout=8)

        self.run_worker(_search_worker(), exclusive=True, group="search", exit_on_error=False)


def main() -> None:
    ScourApp().run()


if __name__ == "__main__":
    main()
