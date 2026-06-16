import logging
from collections.abc import Callable

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import Length, Number
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Log

from key_manager import KeyManager
from log_config import link_textual_ui

logger = logging.getLogger(__name__)


class AddKeyScreen(ModalScreen[tuple[str, str, int]]):
    """Screen with a dialog to add key and interval"""

    def __init__(self, is_duplicate_fn: Callable[[str], bool]) -> None:
        super().__init__()

        self._is_duplicate = is_duplicate_fn
        self.current_priority: int = 5  # Start at 5

    def compose(self) -> ComposeResult:
        with Vertical(id="add-modal-dialog"):
            yield Label("Write a key and an interval in seconds", id="label")
            # Row 1
            with Vertical(classes="input-group"):
                yield Input(
                    placeholder="Key",
                    id="key-input",
                    max_length=1,
                    validators=[
                        Length(
                            minimum=1,
                            maximum=1,
                            failure_description="Key cannot be empty",
                        )
                    ],
                )
                yield Label("", id="key-error", classes="error hidden")

            # Row 2: Interval
            with Vertical(classes="input-group"):
                yield Input(
                    placeholder="Interval (sec)",
                    id="interval-input",
                    type="number",
                    validators=[
                        Number(
                            minimum=0.1, failure_description="Must be greater than 0"
                        )
                    ],
                )
                yield Label("", id="interval-error", classes="error hidden")

            # Row 3: Priority Tracker & Stepper
            with Vertical(id="priority-group"):
                with Horizontal(id="priority-header-row"):
                    yield Label("Priority:", id="priority-title")
                    yield Button("-", id="decrease-prio")
                    yield Label("05", id="prio-display")
                    yield Button("+", id="increase-prio")

                # Crisp single line meter
                yield Label("█" * 20, id="meter-bar")

            # Row 4: Footer
            with Container(id="bottom-container"):
                yield Button("Add", variant="success", id="add-button")
                yield Button("Cancel", variant="primary", id="cancel-button")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Updates and toggles the error labels as the user types."""
        if not event.input or not event.input.id:
            return

        error_label_id = f"#{event.input.id[:-6]}-error"
        error_label = self.query_one(error_label_id, Label)

        if event.validation_result and not event.validation_result.is_valid:
            error_label.update(event.validation_result.failure_descriptions[0])
            error_label.remove_class("hidden")
        else:
            error_label.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "decrease-prio":
            if self.current_priority > 1:
                self.current_priority -= 1
                self._update_priority_ui()

        elif event.button.id == "increase-prio":
            if self.current_priority < 10:
                self.current_priority += 1
                self._update_priority_ui()

        elif event.button.id == "add-button":
            key_input = self.query_one("#key-input", Input)
            interval_input = self.query_one("#interval-input", Input)

            key_input.validate(key_input.value)
            interval_input.validate(interval_input.value)

            if self.query("Input.-invalid"):
                self.notify("Please fill out all fields correctly.", severity="error")
            elif self._is_duplicate(key_input.value):
                self.notify(f"'{key_input.value}' already exists!", severity="warning")
            else:
                self.dismiss(
                    (key_input.value, interval_input.value, self.current_priority)
                )

        elif event.button.id == "cancel-button":
            self.app.pop_screen()

    def _update_priority_ui(self) -> None:
        """Sync the numeric label and the single-line meter width"""
        prio_label = self.query_one("#prio-display", Label)
        prio_label.update(f"{self.current_priority:02d}")

        # At Priority 1: maximum blocks (40)
        # At Prority 10: minimum blocks (6)
        block_map = [40, 35, 30, 22, 20, 18, 16, 10, 8, 6]

        meter = self.query_one("#meter-bar", Label)
        meter.update("█" * block_map[self.current_priority - 1])

        if self.current_priority <= 3:
            meter.styles.color = "red"  # High
        elif self.current_priority <= 7:
            meter.styles.color = "orange"  # Moderate
        else:
            meter.styles.color = "gray"  # Low


class BlueClickerApp(App):
    BINDINGS = [
        ("p", "toggle_pause", "Pause sending"),
        ("p", "toggle_resume", "Resume sending"),
        ("a", "add_key", "Add key"),
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

        if action == "remove_key" and not self._key_manager.has_active_tasks:
            return False

        return True
