import logging

from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import Length, Number
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Log

from key_manager import KeyManager
from log_config import link_textual_ui

logger = logging.getLogger(__name__)


class AddKeyScreen(ModalScreen[tuple[str, str]]):
    """Screen with a dialog to add key and interval"""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Write a key and an interval in seconds", id="label"),
            Input(
                placeholder="Key",
                id="key-input",
                max_length=1,
                validators=[
                    Length(
                        minimum=1, maximum=1, failure_description="Key cannot be empty"
                    )
                ],
            ),
            Input(
                placeholder="Interval (sec)",
                id="interval-input",
                type="number",
                validators=[
                    Number(minimum=0.1, failure_description="Must be greater than 0")
                ],
            ),
            Label("", id="key-error", classes="error"),
            Label("", id="interval-error", classes="error"),
            Button("Add", variant="success", id="add-button"),
            Button("Cancel", variant="primary", id="cancel-button"),
            id="add-dialog",
        )

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
        if event.button.id == "add-button":
            key_input = self.query_one("#key-input", Input)
            interval_input = self.query_one("#interval-input", Input)

            key_input.validate(key_input.value)
            interval_input.validate(interval_input.value)

            if self.query("Input.-invalid"):
                self.notify("Please fill out all fields correctly.", severity="error")
            else:
                self.dismiss((key_input.value, interval_input.value))

        else:
            self.app.pop_screen()


class BlueClickerApp(App):
    BINDINGS = [
        ("p", "toggle_pause", "Pause sending"),
        ("p", "toggle_resume", "Resume sending"),
        ("a", "add_key", "Add key"),
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
        data_table.add_columns("Key", "Interval (sec)")

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
        if self._key_manager.key is None or self._key_manager.interval is None:
            self.notify(
                "Please add any key and its interval before resume.", severity="error"
            )
            return

        self.sending_flag = True
        self._key_manager.toggle_pause(self.sending_flag)

    def action_add_key(self) -> None:
        """An action to display the add key dialog."""

        def get_result(result: tuple[str, str] | None):
            """Called when AddKeyScreen is dismissed."""
            if result is None:
                logger.exception(
                    "AddKeyScreen was dismissed without submitting key and interval"
                )
                return

            key, interval = result
            self.query_one(DataTable).add_row(key, interval)
            self._key_manager.key = key
            self._key_manager.interval = float(interval)
            logger.info(f"Added key: {key} with interval: {interval} sec")

        self.push_screen(AddKeyScreen(), get_result)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "toggle_pause" and not self.sending_flag:
            return False

        if action == "toggle_resume" and self.sending_flag:
            return False

        return True
