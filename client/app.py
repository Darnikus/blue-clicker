import logging

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Log

from key_manager import KeyManager
from log_config import link_textual_ui

logger = logging.getLogger(__name__)


class BlueClickerApp(App):
    BINDINGS = [
        ("p", "toggle_pause", "Pause sending"),
        ("p", "toggle_resume", "Resume sending"),
    ]
    CSS_PATH = "blueclicker.tcss"

    def __init__(self, key_manager: KeyManager) -> None:
        super().__init__()

        self._key_manager = key_manager

    sending_flag: reactive[bool] = reactive(False, bindings=True)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-container"):
            yield Log(auto_scroll=True, id="log")
            yield DataTable(id="key-table")
        yield Footer()

    def on_mount(self) -> None:
        log_widget: Log = self.query_one("#log", Log)
        link_textual_ui(log_widget)

        data_table = self.query_one(DataTable)
        data_table.cursor_type = "row"
        data_table.add_columns("Key", "Interval")

        # TODO Delete next line in next commit
        data_table.add_row(self._key_manager._key, self._key_manager._interval)

        self._background_task = self.run_worker(self._key_manager.start_sending())

    def on_unmount(self) -> None:
        logger.info("App shutting down. Signaling background tasks to stop...")

        self._key_manager.stop_sending()
        self._background_task.cancel()

    def action_toggle_pause(self) -> None:
        """An action to pause sending."""
        self.sending_flag = False
        self._key_manager.toggle_pause(self.sending_flag)

    def action_toggle_resume(self) -> None:
        """An action to resume sending."""
        self.sending_flag = True
        self._key_manager.toggle_pause(self.sending_flag)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "toggle_pause" and not self.sending_flag:
            return False

        if action == "toggle_resume" and self.sending_flag:
            return False

        return True
