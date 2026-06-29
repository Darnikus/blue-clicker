from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label


class SavePresetScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Vertical(id="save-preset-modal-dialog"):
            yield Label("Write a file name and a description", id="label")
            # Row 1: File Name
            with Vertical(classes="input-group"):
                yield Input(
                    placeholder="File Name",
                    id="file-name-input",
                    validators=[
                        Length(
                            minimum=1,
                            failure_description="File name cannot be empty",
                        )
                    ],
                )
                yield Label("", id="file-name-error", classes="error hidden")

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
            filename_input = self.query_one("#file-name-input", Input)
            description_input = self.query_one("#description-input", Input)

            filename_input.validate(filename_input.value)
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
                        filename_input.value,
                        description_input.value,
                    )
                )
