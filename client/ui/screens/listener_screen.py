import logging

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, RichLog

from utility.log_config import active_log_widget

logger = logging.getLogger(__name__)


class ListenerScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("--- API Listener Mode ---")
        yield Label("Waiting for incoming request...")
        with Container():
            yield Button("Stop Listening & Return", id="back-button", variant="error")
        yield RichLog(id="api-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        self._toggle_command_palette(True)

        self._log_token = active_log_widget.set(self.query_one(RichLog))
        logger.info("[green]Listener screen is mounted.[/green]")

    def _on_unmount(self) -> None:
        self._toggle_command_palette(False)
        active_log_widget.reset(self._log_token)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()

    def _toggle_command_palette(self, state: bool) -> None:
        """Removes all commands from the command palette if state is True.\n
        Because custom providers are assigned in App, this method exists."""
        if state:
            self._old_app_commands = self.app.COMMANDS
            self.app.COMMANDS = set()
        else:
            self.app.COMMANDS = self._old_app_commands
