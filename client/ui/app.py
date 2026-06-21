import logging

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Log

from manager.key_manager import KeyManager
from ui.add_key_screen import AddKeyScreen
from ui.edit_key_screen import EditKeyScreen
from utility.log_config import link_textual_ui

logger = logging.getLogger(__name__)


class BlueClickerApp(App):
    BINDINGS = [
        ("p", "toggle_pause", "Pause sending"),
        ("p", "toggle_resume", "Resume sending"),
        ("a", "add_key", "Add key"),
        ("e", "edit_key", "Edit key"),
        ("r", "remove_key", "Remove key"),
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
        columns = ("Key", "Interval (sec)", "Priority")
        for name in columns:
            data_table.add_column(name, key=name)

        # self._background_task = self.run_worker(self._key_manager.start_sending())
        self._key_manager.start()

    def on_unmount(self) -> None:
        logger.info("App shutting down. Signaling background tasks to stop...")

        self._key_manager.shutdown()
        # self._background_task.cancel()

    def action_toggle_pause(self) -> None:
        """An action to pause sending."""
        self.sending_flag = False
        self._key_manager.toggle_pause(self.sending_flag)

    def action_toggle_resume(self) -> None:
        """An action to resume sending."""
        if not self._key_manager.has_active_tasks:
            self.notify(
                "Please add any key and its interval before resume.", severity="error"
            )
            return

        self.sending_flag = True
        self._key_manager.toggle_pause(self.sending_flag)

    def action_add_key(self) -> None:
        """An action to display the add key dialog."""

        def get_result(result: tuple[str, str, int] | None):
            """Called when AddKeyScreen is dismissed."""
            if result is None:
                logger.exception(
                    "AddKeyScreen was dismissed without submitting key and interval"
                )
                return

            key, interval, priority = result
            data_table = self.query_one(DataTable)
            row_key = data_table.add_row(key, interval, priority)
            data_table.sort("Priority")

            self._key_manager.add_key(str(row_key), key, float(interval), priority)
            logger.info(
                f"Added key: {key} with interval: {interval} sec"
                + f" and {priority} priority"
            )

        self.push_screen(
            AddKeyScreen(is_duplicate_fn=self._key_manager.is_duplicate), get_result
        )

    def action_edit_key(self) -> None:
        """An action to display the edit key screen."""
        data_table = self.query_one(DataTable)
        row_key, _ = data_table.coordinate_to_cell_key(data_table.cursor_coordinate)

        def get_result(result: tuple[str, int] | None) -> None:
            if result is None:
                logger.exception(
                    "EditKeyScreen was dismissed without submitting interval"
                )
                return

            interval, priority = result
            data_table.update_cell(row_key, "Interval (sec)", value=interval)
            data_table.update_cell(row_key, "Priority", value=priority)
            self._key_manager.edit_key(str(row_key), float(interval), priority)

        values = data_table.get_row(row_key)
        self.push_screen(EditKeyScreen(*values), get_result)

    def action_remove_key(self) -> None:
        """An action to remove key and its interval"""
        data_table = self.query_one(DataTable)
        row_key, _ = data_table.coordinate_to_cell_key(data_table.cursor_coordinate)

        self._key_manager.remove_key(str(row_key))
        data_table.remove_row(row_key)

        # Tell Textual to re-run check_action method
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "toggle_pause" and not self.sending_flag:
            return False

        if action == "toggle_resume" and self.sending_flag:
            return False

        if action == "edit_key" and not self._key_manager.has_active_tasks:
            return False

        if action == "remove_key" and not self._key_manager.has_active_tasks:
            return False

        return True
