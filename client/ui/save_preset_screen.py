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
                yield Button("Save", variant="success", id="add-button")
                yield Button("Cancel", variant="primary", id="cancel-button")
