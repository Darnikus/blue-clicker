from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label


class SavePresetScreen(ModalScreen[tuple[str, str | None]]):
    def compose(self) -> ComposeResult:
        with Vertical(id="save-preset-modal-dialog"):
            yield Label("Write a filename and a description", id="label")
            # Row 1: Filename
            with Vertical(classes="input-group"):
                yield Input(
                    placeholder="Filename",
                    id="filename-input",
                    validators=[
                        Length(
                            minimum=1,
                            failure_description="Filename cannot be empty",
                        )
                    ],
                )
                yield Label("", id="filename-error", classes="error hidden")

            # Row 2: Description
            with Vertical(classes="input-group"):
                yield Input(
                    placeholder="Description (optional)",
                    id="description-input",
                )
                # yield Label("", id="description-error", classes="error hidden")

            # Row 3: Footer
            with Container(id="bottom-container"):
                yield Button("Save", variant="success", id="save-button")
                yield Button("Cancel", variant="primary", id="cancel-button")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Updates and toggles the error labels as the user types."""
        if not event.input or not event.input.id:
            return

        # I don't want to have validation for description yet
        if event.input.id[:-6] == "description":
            return

        error_label_id = f"#{event.input.id[:-6]}-error"
        error_label = self.query_one(error_label_id, Label)

        if event.validation_result and not event.validation_result.is_valid:
            error_label.update(event.validation_result.failure_descriptions[0])
            error_label.remove_class("hidden")
        else:
            error_label.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            self.app.pop_screen()

        elif event.button.id == "save-button":
            file_name_input = self.query_one("#filename-input", Input)
            description_input = self.query_one("#description-input", Input)

            file_name_input.validate(file_name_input.value)
            # description_input.validate(description_input.value)

            if self.query("Input.-invalid"):
                self.notify("Please fill out all fields correctly.", severity="error")
            # elif self._is_duplicate(filename_input.value):
            #     self.notify(
            #         f"'{filename_input.value}' already exists!", severity="warning"
            #     )
            else:
                self.dismiss(
                    (
                        file_name_input.value,
                        description_input.value,
                    )
                )
