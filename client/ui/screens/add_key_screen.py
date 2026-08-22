from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length, Number
from textual.widgets import Button, Input, Label

from ui.widgets.priority_slider import PrioritySlider


class AddKeyScreen(ModalScreen[tuple[str, str, int]]):
    """Dialog screen to add key and interval.

    Attributes:
        _is_duplicate (Callable[[str], bool]): The function to check key duplications.
        _current_priority (int): A key's current priority.
    """

    def __init__(self, is_duplicate_fn: Callable[[str], bool]) -> None:
        super().__init__()

        self._is_duplicate = is_duplicate_fn
        self._current_priority: int = 5  # Start at 5

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
                    yield Label("05", id="prio-display")
                    yield Label("(Click, Drag, < >)", id="prio-help")

                # Crisp single line meter
                yield PrioritySlider(id="meter-bar")

            # Row 4: Footer
            with Container(id="bottom-container"):
                yield Button("Add", variant="success", id="add-button")
                yield Button("Cancel", variant="primary", id="cancel-button")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Updates and toggles the error labels as the user types.

        Args:
            event (Input.Changed): Posted whenever the input's value changes.
        """
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
        """The message handler is called when any button is pressed.

        Args:
            event (Button.Pressed): Event sent when a Button is pressed.
        """
        if event.button.id == "add-button":
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
                    (key_input.value, interval_input.value, self._current_priority)
                )

        elif event.button.id == "cancel-button":
            self.app.pop_screen()

    def on_priority_slider_changed(self, message: PrioritySlider.Changed) -> None:
        """Listens for custom PrioritySlider.Changed messages and updates the UI.

        Args:
            message (PrioritySlider.Changed): A broadcast announcing a priority change.
        """
        self._current_priority = message.value
        prio_label = self.query_one("#prio-display", Label)
        prio_label.update(f"{self._current_priority:02d}")
