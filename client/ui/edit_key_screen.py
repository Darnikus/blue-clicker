from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Number
from textual.widgets import Button, Input, Label


class EditKeyScreen(ModalScreen[tuple[float, int]]):
    """Screen with a dialog to edit key's interval and priority"""

    # At Priority 1: maximum blocks (40)
    # At Prority 10: minimum blocks (6)
    _BLOCK_MAP: list[int] = [40, 35, 30, 22, 20, 18, 16, 10, 8, 6]

    def __init__(self, key: str, old_interval: float, old_priority: int) -> None:
        super().__init__()

        self._key = key
        self._interval: float = old_interval
        self._priority: int = old_priority

    def compose(self) -> ComposeResult:
        with Vertical(id="edit-modal-dialog"):
            yield Label(f"Edit '{self._key}' interval and priority", id="label")

            # Row 1: Interval
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
                    value=str(self._interval),
                )
                yield Label("", id="interval-error", classes="error hidden")

            # Row 2: Priority Tracker & Stepper
            with Vertical(id="priority-group"):
                with Horizontal(id="priority-header-row"):
                    yield Label("Priority:", id="priority-title")
                    yield Button("-", id="decrease-prio")
                    yield Label("05", id="prio-display")
                    yield Button("+", id="increase-prio")

                # Crisp single line meter
                yield Label("█" * 20, id="meter-bar")

            # Row 3: Footer
            with Container(id="bottom-container"):
                yield Button("Save", variant="success", id="save-button")
                yield Button("Cancel", variant="primary", id="cancel-button")

    def on_mount(self) -> None:
        self._update_priority_ui()

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
            if self._priority > 1:
                self._priority -= 1
                self._update_priority_ui()

        elif event.button.id == "increase-prio":
            if self._priority < 10:
                self._priority += 1
                self._update_priority_ui()

        elif event.button.id == "save-button":
            interval_input = self.query_one("#interval-input", Input)

            interval_input.validate(interval_input.value)

            if self.query("Input.-invalid"):
                self.notify("Please fill out all fields correctly.", severity="error")
            else:
                ...
                # self.dismiss(
                #     (key_input.value, interval_input.value, self.current_priority)
                # )
                # TODO Add edit logic

        elif event.button.id == "cancel-button":
            self.app.pop_screen()

    def _update_priority_ui(self) -> None:
        """Sync the numeric label and the single-line meter width"""
        prio_label = self.query_one("#prio-display", Label)
        prio_label.update(f"{self._priority:02d}")

        meter = self.query_one("#meter-bar", Label)
        meter.update("█" * self._BLOCK_MAP[self._priority - 1])

        if self._priority <= 3:
            meter.styles.color = "red"  # High
        elif self._priority <= 7:
            meter.styles.color = "orange"  # Moderate
        else:
            meter.styles.color = "gray"  # Low
