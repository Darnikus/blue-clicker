import json

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

    .hidden {
        display: none;
    }

}
"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="load-modal-screen"):
            yield DirectoryTree("./presets")

            with Vertical(id="main-panel"):
                yield Label("Select a file from the sidebar to begin", id="file-title")
                yield Label(id="description-label")

                yield DataTable()

                with Horizontal(id="button-container"):
                    yield Button(
                        "Load", variant="success", id="load-button", classes="hidden"
                    )
                    yield Button("Cancel", variant="error", id="cancel-button")

    def on_mount(self) -> None:
        self.query_one(DataTable).cursor_type = "none"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            self.app.pop_screen()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        if event.path.suffix == ".json":
            self.query_one("#file-title", Label).update(
                f"📄 File: [u]{event.path.name}[/u]"
            )

            with open(event.path) as file:
                data = json.load(file)

            table = self.query_one(DataTable)
            table.clear(columns=True)
            load_button = self.query_one("#load-button", Button)

            if data:
                self.query_one("#description-label", Label).update(
                    f"Description: {data['description']}"
                )

                columns = ("Key", "Interval (sec)", "Priority")
                for name in columns:
                    table.add_column(name, key=name)

                for row in data["keys"]:
                    table.add_row(*row.values())
                table.sort("Priority")

                if load_button.has_class("hidden"):
                    load_button.remove_class("hidden")


class TestApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Open Modal")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(LoadPresetScreen())


if __name__ == "__main__":
    TestApp().run()
