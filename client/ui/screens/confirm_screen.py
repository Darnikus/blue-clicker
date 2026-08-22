from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmScreen(ModalScreen[bool | None]):
    """Dialog screen for confirming navigation to ListenerScreen."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(
                "Are you sure you want to move to the Listener Mode?\n"
                + "All current keys will be removed.",
                id="question",
            ),
            Button("Yes", variant="error", id="confirm-button"),
            Button("Cancel", variant="primary", id="cancel-button"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """The message handler is called when any button is pressed.

        Args:
            event (Button.Pressed): Event sent when a Button is pressed.
        """
        if event.button.id == "confirm-button":
            self.dismiss(True)
        else:
            self.app.pop_screen()
