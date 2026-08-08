from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, RichLog


class ListenerScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("--- API Listener Mode ---")
        yield Label("Waiting for incoming request...")
        with Container():
            yield Button("Stop Listening & Return", id="back-button", variant="error")
        yield RichLog(id="api-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        log.write("[green]Listener screen is mounted.[/green]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()
