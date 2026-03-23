import subprocess
import sys

from textual.app import App, ComposeResult
from textual.widgets import ContentSwitcher, Input

from scour.models import PipelineError
from scour.pipeline import run_search
from scour.utils import results_dir
from scour.widgets.history import HistoryView, ReportSelected
from scour.widgets.loading import LoadingView
from scour.widgets.report_preview import ReportPreview
from scour.widgets.results import ResultsView
from scour.widgets.welcome import HelpView, TipsView, WelcomeView


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
        self._nav_stack: list[str] = []
        self._command_history: list[str] = []
        self._history_cursor: int = -1

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="welcome", id="main-content"):
            yield WelcomeView(id="welcome")
            yield HelpView(id="help")
            yield TipsView(id="tips")
            yield LoadingView(id="loading")
            yield ResultsView(id="results")
            yield HistoryView(id="history")
            yield ReportPreview(id="preview")
        yield Input(placeholder='/search "query" | /history | /tips | /help | /quit', id="command-bar")

    def on_mount(self) -> None:
        self.query_one("#command-bar", Input).focus()

    def _switch_to(self, view_id: str) -> None:
        switcher = self.query_one("#main-content", ContentSwitcher)
        current = switcher.current
        if current != view_id:
            self._nav_stack.append(current)
        switcher.current = view_id
        command_bar = self.query_one("#command-bar", Input)
        if view_id == "preview":
            command_bar.display = False
            self.query_one("#preview-scroll").focus()
        else:
            command_bar.display = True
            command_bar.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if raw:
            self._command_history.append(raw)
            self._history_cursor = -1
        event.input.clear()
        if not raw:
            return

        if raw.startswith("/search "):
            rest = raw[8:].strip()
            top_n = 5
            if rest.startswith("-n "):
                parts = rest.split(None, 2)
                if len(parts) >= 2 and parts[1].isdigit():
                    top_n = max(2, min(15, int(parts[1])))
                    rest = parts[2] if len(parts) > 2 else ""
                else:
                    self.notify('Usage: /search -n 5 "your query"', severity="warning")
                    return
            query = rest.strip('"').strip("'")
            if query:
                self._do_search(query, top_n=top_n)
            else:
                self.notify('Usage: /search "your query"', severity="warning")

        elif raw == "/history":
            self._switch_to("history")
            self.query_one(HistoryView).refresh_list()

        elif raw == "/help":
            self._switch_to("help")

        elif raw == "/tips":
            self._switch_to("tips")

        elif raw == "/clear":
            self._nav_stack.clear()
            self.query_one("#main-content", ContentSwitcher).current = "welcome"

        elif raw == "/rerun":
            preview = self.query_one(ReportPreview)
            if preview.current_query:
                self._do_search(preview.current_query)
            else:
                self.notify("No report loaded to re-run", severity="warning")

        elif raw == "/delete":
            current = self.query_one("#main-content", ContentSwitcher).current
            if current == "history":
                self.query_one(HistoryView).action_delete_selected()
            else:
                self.notify("Use /delete from the history view", severity="warning")

        elif raw == "/copy":
            self._copy_report()

        elif raw == "/open":
            self._open_results_dir()

        elif raw == "/doom":
            self._launch_doom()

        elif raw in ("/quit", "/exit"):
            self.exit()

        else:
            self.notify(f"Unknown command: {raw}", severity="warning")

    def on_key(self, event) -> None:
        input_widget = self.query_one("#command-bar", Input)
        if event.key == "up" and self._command_history:
            if self._history_cursor == -1:
                self._history_cursor = len(self._command_history) - 1
            elif self._history_cursor > 0:
                self._history_cursor -= 1
            input_widget.value = self._command_history[self._history_cursor]
            input_widget.cursor_position = len(input_widget.value)
            event.prevent_default()
        elif event.key == "down" and self._history_cursor != -1:
            if self._history_cursor < len(self._command_history) - 1:
                self._history_cursor += 1
                input_widget.value = self._command_history[self._history_cursor]
            else:
                self._history_cursor = -1
                input_widget.value = ""
            input_widget.cursor_position = len(input_widget.value)
            event.prevent_default()
        elif event.key == "escape":
            current = self.query_one("#main-content", ContentSwitcher).current
            if current in ("preview", "history", "help", "tips"):
                if self._nav_stack:
                    target = self._nav_stack.pop()
                else:
                    target = "welcome"
                self.query_one("#main-content", ContentSwitcher).current = target
                # Restore command bar if leaving preview
                if current == "preview":
                    command_bar = self.query_one("#command-bar", Input)
                    command_bar.display = True
            input_widget.focus()
        elif event.key == "shift+tab":
            current = self.query_one("#main-content", ContentSwitcher).current
            if current != "results":
                self._nav_stack.clear()
                self._nav_stack.append("welcome")
                self.query_one("#main-content", ContentSwitcher).current = "results"
            input_widget.focus()
        elif event.key == "d":
            current = self.query_one("#main-content", ContentSwitcher).current
            if current == "history" and not input_widget.has_focus:
                self.query_one(HistoryView).action_delete_selected()

    def on_report_selected(self, event: ReportSelected) -> None:
        self._switch_to("preview")
        self.query_one(ReportPreview).show_report(event.path)

    def _copy_report(self) -> None:
        results_view = self.query_one(ResultsView)
        report = results_view._report
        if not report or not report.markdown:
            self.notify("No report to copy — run /search first", severity="warning")
            return
        try:
            if sys.platform == "darwin":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            else:
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(report.markdown.encode())
            self.notify("Report copied to clipboard", severity="information")
        except FileNotFoundError:
            self.notify(f"Report saved at: {report.saved_path}", severity="information")

    def _open_results_dir(self) -> None:
        path = str(results_dir())
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            self.notify(f"Opened {path}", severity="information")
        except FileNotFoundError:
            self.notify(f"Reports are at: {path}", severity="information")

    def _launch_doom(self) -> None:
        from scour.doom import run_doom, _is_built, _supports_kitty_graphics

        if _supports_kitty_graphics() and not _is_built():
            self.notify("Building terminal-doom (one-time setup)...", severity="information", timeout=10)

        def _on_status(msg: str) -> None:
            self.notify(msg, severity="information", timeout=8)

        with self.suspend():
            run_doom(on_status=_on_status)
        self.query_one("#command-bar", Input).focus()

    def _do_search(self, query: str, top_n: int = 5) -> None:
        async def _search_worker() -> None:
            loading = self.query_one(LoadingView)
            self._switch_to("loading")
            loading.set_status("Starting search...")
            loading.start_timer()

            def on_status(msg: str) -> None:
                loading.set_status(msg)

            try:
                report = await run_search(query, on_status, top_n=top_n)
                loading.stop_timer()
                results_view = self.query_one(ResultsView)
                results_view.show_report(report)
                self._switch_to("results")
                self.notify(f"Report saved to {report.saved_path}", severity="information")
            except PipelineError as e:
                loading.stop_timer()
                self._switch_to("welcome")
                self.notify(str(e), severity="error", timeout=8)
            except Exception as e:
                loading.stop_timer()
                self._switch_to("welcome")
                self.notify(f"Unexpected error: {e}", severity="error", timeout=8)

        self.run_worker(_search_worker(), exclusive=True, group="search", exit_on_error=False)


def main() -> None:
    ScourApp().run()


if __name__ == "__main__":
    main()
