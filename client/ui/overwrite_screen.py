from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class OverwriteScreen(ModalScreen[bool | None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="ovewrite-modal-dialog"):
            yield Label(
                "⚠️ A file with this name already exists. Overwrite?", id="label"
            )

            # Row 1: Footer
            with Container(id="bottom-container"):
                yield Button("Overwrite", variant="success", id="save-button")
                yield Button("Cancel", variant="primary", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            self.app.pop_screen()

        elif event.button.id == "save-button":
            self.dismiss(True)
