from collections.abc import Callable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, DirectoryTree, Label

from manager.preview_preset import PreviewPreset


class LoadPresetScreen(ModalScreen[Path | None]):
    def __init__(self, file_preview_fn: Callable[[Path], PreviewPreset]) -> None:
        super().__init__()

        self._file_preview_callback = file_preview_fn
        self._selected_file_path: Path | None = None

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

        elif event.button.id == "load-button":
            self.dismiss(self._selected_file_path)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        if event.path.suffix == ".json":
            self.query_one("#file-title", Label).update(
                f"📄 File: [u]{event.path.name}[/u]"
            )

            self._selected_file_path = event.path

            preview = self._file_preview_callback(event.path)

            table = self.query_one(DataTable)
            table.clear(columns=True)
            load_button = self.query_one("#load-button", Button)

            if preview:
                self.query_one("#description-label", Label).update(
                    f"Description: {preview.description}"
                )

                columns = ("Key", "Interval (sec)", "Priority")
                for name in columns:
                    table.add_column(name, key=name)

                for row in preview.keys:
                    table.add_row(*row.values())
                table.sort("Priority")

                if load_button.has_class("hidden"):
                    load_button.remove_class("hidden")
