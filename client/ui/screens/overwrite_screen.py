from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class OverwriteScreen(ModalScreen[bool | None]):
    """Dialog screen for confirming preset file overwrite."""

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
        """The message handler is called when any button is pressed.

        Args:
            event (Button.Pressed): Event sent when a Button is pressed.
        """
        if event.button.id == "cancel-button":
            self.app.pop_screen()

        elif event.button.id == "save-button":
            self.dismiss(True)
