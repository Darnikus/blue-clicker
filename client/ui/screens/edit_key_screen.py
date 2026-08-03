from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Number
from textual.widgets import Button, Input, Label

from ui.widgets.priority_slider import PrioritySlider


class EditKeyScreen(ModalScreen[tuple[str, int]]):
    """Screen with a dialog to edit key's interval and priority"""

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
                    yield Label(f"{self._priority:02d}", id="prio-display")
                    yield Label("(Click, Drag, < >)", id="prio-help")

                # Crisp single line meter
                yield PrioritySlider(initial_value=self._priority, id="meter-bar")

            # Row 3: Footer
            with Container(id="bottom-container"):
                yield Button("Save", variant="success", id="save-button")
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
        if event.button.id == "save-button":
            interval_input = self.query_one("#interval-input", Input)

            interval_input.validate(interval_input.value)

            if self.query("Input.-invalid"):
                self.notify("Please fill out all fields correctly.", severity="error")
            else:
                self.dismiss((interval_input.value, self._priority))

        elif event.button.id == "cancel-button":
            self.app.pop_screen()

    def on_priority_slider_changed(self, message: PrioritySlider.Changed) -> None:
        """Listens for custom PrioritySlider.Changed messages and updates the UI."""
        self._priority = message.value
        prio_label = self.query_one("#prio-display", Label)
        prio_label.update(f"{self._priority:02d}")
