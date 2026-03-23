from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option

from scour.utils import list_reports, parse_report_meta


class ReportSelected(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class HistoryView(Widget):
    DEFAULT_CSS = """
    HistoryView {
        height: 1fr;
        padding: 1 2;
    }
    HistoryView #history-header {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }
    HistoryView #empty-msg {
        color: $text-muted;
        text-style: italic;
    }
    HistoryView OptionList {
        border: round $panel;
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._paths: list[Path] = []

    def compose(self) -> ComposeResult:
        yield Label(
            "Past Reports  [dim](Escape to go back | d to delete)[/dim]",
            id="history-header",
            markup=True,
        )
        yield Label("No reports found. Run /search to create one.", id="empty-msg")
        yield OptionList(id="report-list")

    def refresh_list(self) -> None:
        self._paths = list_reports()
        option_list = self.query_one("#report-list", OptionList)
        empty_msg = self.query_one("#empty-msg", Label)
        option_list.clear_options()

        if not self._paths:
            empty_msg.display = True
            option_list.display = False
            return

        empty_msg.display = False
        option_list.display = True
        for path in self._paths:
            date_label, query = parse_report_meta(path)
            display_name = f"{date_label}  {query}" if query else path.name
            # Truncate long display names
            if len(display_name) > 80:
                display_name = display_name[:77] + "..."
            option_list.add_option(Option(display_name, id=str(path)))
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.post_message(ReportSelected(Path(event.option.id)))

    def action_delete_selected(self) -> None:
        option_list = self.query_one("#report-list", OptionList)
        idx = option_list.highlighted
        if idx is None or idx < 0 or idx >= len(self._paths):
            return
        path = self._paths[idx]
        try:
            path.unlink()
        except Exception:
            return
        self.refresh_list()
