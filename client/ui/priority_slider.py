from rich.console import RenderableType
from textual.events import Key, MouseDown, MouseMove
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label


class PrioritySlider(Label):
    """A custom priority slider widget."""

    DEFAULT_CSS = """
PrioritySlider {
        background: $surface;
        height: 1;
        margin-top: 0;
    }
"""
    value = reactive(0)

    class Changed(Message):
        """Broadcast priority changes to a parent."""

        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value

    def __init__(
        self,
        min_value: int = 0,
        max_value: int = 10,
        initial_value: int = 5,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(initial_value, max_value))
        self.can_focus = True  # Allows keyboard interaction

    def render(self) -> RenderableType:
        """Draws the slider."""
        width = self.size.width or 40

        total_span = self.max_value - self.min_value
        inverted_value = self.max_value - (self.value - self.min_value)
        cursor_position = int(
            ((inverted_value - self.min_value) / total_span) * (width - 1)
        )

        left_side = "█" * cursor_position
        cursor = "█"

        if self.value <= 3:
            color = "red"  # High
        elif self.value <= 7:
            color = "orange"  # Moderate
        else:
            color = "gray"  # Low

        return f"[{color}]{left_side}{cursor}[/]"

    def on_key(self, event: Key) -> None:
        """Handles left/right arrow movements"""
        if event.key == "left":
            self._update_priority(self.value + 1)
        elif event.key == "right":
            self._update_priority(self.value - 1)

    def on_mouse_down(self, event: MouseDown) -> None:
        """Handles single click on the slider track."""
        self.focus()
        self._update_value_from_offset(event.x)

    def on_mouse_move(self, event: MouseMove) -> None:
        """Handls drag on the slider track."""
        if event.button == 1:
            self._update_value_from_offset(event.x)

    def watch_value(self) -> None:
        """Forces a re-render when the priority value state mutates."""
        self.refresh()

    def _update_priority(self, value: int) -> None:
        """Safely mutates the priority state"""
        new_value = max(0, min(value, 10))
        if new_value != self.value:
            self.value = new_value
            self.post_message(self.Changed(self.value))

    def _update_value_from_offset(self, x_offset: int) -> None:
        """Translates a click into a slider value."""
        width = self.size.width
        if width <= 2:
            return

        percentage = max(0.0, min(1.0, (x_offset - 1) / (width - 3)))
        new_value = self.min_value + round(
            percentage * (self.max_value - self.min_value)
        )
        new_value = (
            self.max_value + self.min_value - new_value
        )  # Need to reverse the value

        self._update_priority(new_value)
