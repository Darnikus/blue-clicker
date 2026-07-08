from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, DirectoryTree, Label


class LoadPresetScreen(ModalScreen):
    CSS = """
LoadPresetScreen {
    align: center middle;

    #load-modal-screen {
        width: 85;
        height: auto;
        max-height: 85%;
        background: $panel;
        padding: 1;
        border: tab $secondary; /* This and padding maybe delete if i will chnage the design */
    }

    DirectoryTree {
        width: 25;
        height: 100%;
        border-right: wide $primary;
    }

    #main-panel {
        width: 1fr;
        height: auto;
    }

    #file-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
        padding-left: 2;
    }

    #description-label {
        width: 100%;
        height: auto;
        text-wrap: wrap;
        margin-bottom: 1;
        padding-left: 2;
        text-style: italic;
        color: $text;
    }

    DataTable {
        width: 100%;
        height: auto;
        max-height: 12;
        margin-left: 2;
    }

    #button-container {
        height: auto;
        margin-top: 1;
        padding-left: 2;
        align-horizontal: right;
    }

    #cancel-button {
        margin-left: 2;
    }

}
"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="load-modal-screen"):
            yield DirectoryTree("./presets")

            with Vertical(id="main-panel"):
                yield Label("📄 File: None", id="file-title")
                yield Label(
                    "Description: Choose a file from the tree view to pull dynamic layout presets. "
                    "If this text gets incredibly long because of verbose notes, it automatically wraps "
                    "gracefully onto new lines.",
                    id="description-label",
                )

                yield DataTable()

                with Horizontal(id="button-container"):
                    yield Button("Load", variant="success", id="load-button")
                    yield Button("Cancel", variant="error", id="cancel-button")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("Key", "Interval (sec)", "Priority")
        for i in range(10):  # Test data for ui
            table.add_row(f"{i}", f"{i * 10}", "10")


class TestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Open Modal")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(LoadPresetScreen())


if __name__ == "__main__":
    TestApp().run()
