from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option

from scour.utils import list_reports


class ReportSelected(Message):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class HistoryView(Widget):
    DEFAULT_CSS = """
    HistoryView {
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
        yield Label("Past Reports", id="history-header")
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
            option_list.add_option(Option(path.name, id=str(path)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.post_message(ReportSelected(Path(event.option.id)))
