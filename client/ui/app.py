import logging
from pathlib import Path
from typing import cast

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Header, RichLog

from manager.key_manager import KeyManager
from ui.providers.load_preset_provider import LoadPresetProvider
from ui.providers.open_listener_provider import OpenListenerProvider
from ui.providers.save_preset_provider import SavePresetProvider
from ui.screens.add_key_screen import AddKeyScreen
from ui.screens.edit_key_screen import EditKeyScreen
from ui.screens.listener_screen import ListenerScreen
from ui.screens.load_preset_screen import LoadPresetScreen
from ui.screens.save_preset_screen import SavePresetScreen
from ui.widgets.key_cooldown import KeyCooldown
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
    COMMANDS = App.COMMANDS | {
        LoadPresetProvider,
        SavePresetProvider,
        OpenListenerProvider,
    }
    CSS_PATH = "blueclicker.tcss"

    def __init__(self, key_manager: KeyManager) -> None:
        super().__init__()

        self._key_manager = key_manager

    sending_flag: reactive[bool] = reactive(False, bindings=True)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-container"):
            yield RichLog(auto_scroll=True, highlight=True, markup=True, id="log")
            yield DataTable(id="key-table")
            yield VerticalScroll(id="key-cooldown")  # change to with
        yield Footer()

    def on_mount(self) -> None:
        log_widget: RichLog = self.query_one("#log", RichLog)
        link_textual_ui(log_widget)

        data_table = self.query_one(DataTable)
        data_table.cursor_type = "row"
        columns = ("Key", "Interval (sec)", "Priority")
        for name in columns:
            data_table.add_column(name, key=name)

        # self._background_task = self.run_worker(self._key_manager.start_sending())
        self._key_manager.start()

    async def on_unmount(self) -> None:
        logger.info("App shutting down. Signaling background tasks to stop...")

        await self._key_manager.shutdown()
        # self._background_task.cancel()

    def action_toggle_pause(self) -> None:
        """An action to pause sending."""
        self.sending_flag = False
        self._key_manager.toggle_pause(self.sending_flag)
        self._toggle_key_cooldown_pause()

    def action_toggle_resume(self) -> None:
        """An action to resume sending."""
        if not self._key_manager.has_active_tasks:
            self.notify(
                "Please add any key and its interval before resume.", severity="error"
            )
            return

        self.sending_flag = True
        self._key_manager.toggle_pause(self.sending_flag)
        self._toggle_key_cooldown_pause()

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
            row_key, attach_callable = self._key_manager.add_key(
                key, float(interval), priority
            )

            data_table = self.query_one(DataTable)
            data_table.add_row(key, interval, priority, key=row_key)
            data_table.sort("Priority")

            cooldown_container = self.query_one("#key-cooldown", VerticalScroll)
            cooldown_container.mount(
                KeyCooldown(
                    row_key, key, float(interval), self.sending_flag, attach_callable
                )
            )
            self._sort_cooldown_container(cooldown_container)

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
            self._key_manager.edit_key(str(row_key.value), float(interval), priority)
            data_table.update_cell(row_key, "Interval (sec)", value=interval)
            data_table.update_cell(row_key, "Priority", value=priority)
            data_table.sort("Priority")

            cooldown_container = self.query_one("#key-cooldown", VerticalScroll)
            widget = self._get_key_cooldown_widget(cooldown_container, row_key.value)
            if widget is not None:
                widget.duration = float(interval)
            self._sort_cooldown_container(cooldown_container)

        values = data_table.get_row(row_key)
        self.push_screen(EditKeyScreen(*values), get_result)

    def action_remove_key(self) -> None:
        """An action to remove key and its interval"""
        data_table = self.query_one(DataTable)
        row_key, _ = data_table.coordinate_to_cell_key(data_table.cursor_coordinate)

        self._key_manager.remove_key(str(row_key.value))
        data_table.remove_row(row_key)

        cooldown_container = self.query_one("#key-cooldown", VerticalScroll)
        widget = self._get_key_cooldown_widget(cooldown_container, row_key.value)
        if widget is not None:
            widget.remove()
            self._sort_cooldown_container(cooldown_container)

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

    def load_preset(self) -> None:
        if not self._key_manager.has_preset_files():
            self.notify(
                "There is nothing to load. Save a preset first.", severity="warning"
            )
            return

        data_table = self.query_one(DataTable)
        cooldown_container = self.query_one("#key-cooldown", VerticalScroll)

        async def get_result(result: Path | None) -> None:
            assert isinstance(result, Path), (
                f"Expected Path, got {type(result).__name__}"
            )
            rows, attach_callbacks = await self._key_manager.load_preset_from_file(
                result
            )
            data_table.clear()
            cooldown_container.remove_children()
            for (key_row, row), callback in zip(
                rows.items(), attach_callbacks, strict=False
            ):
                row["interval"] = f"{row['interval']:g}"
                data_table.add_row(*row.values(), key=key_row)
                cooldown_container.mount(
                    KeyCooldown(
                        key_row,
                        row["key"],
                        float(row["interval"]),
                        self.sending_flag,
                        callback,
                    )
                )
            data_table.sort("Priority")
            self._sort_cooldown_container(cooldown_container)
            logger.info(f"Preset from '{result.name}' has been loaded")

        self.push_screen(
            LoadPresetScreen(file_preview_fn=self._key_manager.get_file_preview),
            get_result,
        )

    def save_preset(self) -> None:
        data_table = self.query_one(DataTable)

        if data_table.row_count < 1:
            self.notify(
                "Cannot save: The table is currently empty.", severity="warning"
            )
            return

        def get_result(result: tuple[str, str | None] | None) -> None:
            match result:
                case None:
                    logger.exception(
                        "SavePresetScreen was dismissed without submitting filename."
                    )
                case (file_name, description):
                    self._key_manager.save_keys_to_file(file_name, description)

        self.push_screen(
            SavePresetScreen(file_exists_fn=self._key_manager.file_exists),
            get_result,
        )

    def open_listener(self) -> None:
        self.push_screen(ListenerScreen())

    def _get_key_cooldown_widget(
        self, cooldown_container: VerticalScroll, row_key: str | None
    ) -> KeyCooldown | None:
        return next(
            (
                x
                for x in cooldown_container.children
                if isinstance(x, KeyCooldown) and x.key_id == row_key
            ),
            None,
        )

    def _sort_cooldown_container(self, container: VerticalScroll) -> None:

        def get_cooldown_duration(widget: Widget) -> float:
            widget = cast(KeyCooldown, widget)
            return widget.duration

        container.sort_children(key=get_cooldown_duration, reverse=True)

    def _toggle_key_cooldown_pause(self) -> None:
        container = self.query_one("#key-cooldown", VerticalScroll)
        for widget in container.children:
            if isinstance(widget, KeyCooldown):
                widget.is_paused = not self.sending_flag  # Same comment about flag
