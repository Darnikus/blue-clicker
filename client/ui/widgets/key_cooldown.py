from collections.abc import Callable
from time import monotonic

from rich.console import RenderableType
from rich.text import Text
from textual.color import Gradient
from textual.reactive import reactive
from textual.widgets import Static


class KeyCooldown(Static):
    DEFAULT_CSS = """
        KeyCooldown {
            color: white;
            background: black;
            text-style: bold;
        }
    """

    duration = reactive(0.0)
    remaining_time = reactive(0.0)

    def __init__(
        self,
        key_id: str,
        key: str,
        duration: float,
        attach_callable: Callable[[Callable[[float], None]], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.key_id = key_id
        self._key: str = key
        self.duration = duration
        self._anchor_time = monotonic()

        self._gradient = Gradient.from_colors("dimgray", "darkorange", "red")

        self._attach_callable: Callable[[Callable[[float], None]], None] = (
            attach_callable
        )

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self._attach_callable(
            self._update_duration
        )  # Subscribe here, because i need to wait for next notify if do it in init
        self._countdown_timer = self.set_interval(
            1 / 100, self._update_remaining_time, pause=True
        )  # maybe change interval to 1 / 60

    def render(self) -> RenderableType:
        width = self.size.width or 40
        height = self.size.height or 3

        progress_ratio = 1 - (
            self.remaining_time / self.duration
        )  # line goes from left to right
        fill_width = int(width * progress_ratio)

        message = f"{self._key} - {self._cooldown_text}"
        output_text = Text()
        mid_y = height // 2

        fallback_bg = (
            self.styles.background.hex
            if self.styles.background and not self.styles.background.is_transparent
            else "#1e1e1e"
        )

        for y in range(height):
            for x in range(width):
                if x < fill_width:
                    ratio = x / width if width > 0 else 0
                    bg_color = self._gradient.get_color(ratio).hex
                else:
                    bg_color = fallback_bg

                char = " "
                fg_color = self.styles.color.hex if self.styles.color else "black"

                if y == mid_y:
                    start_x = (width - len(message)) // 2
                    if start_x <= x < start_x + len(message):
                        char = message[x - start_x]

                output_text.append(char, style=f"{fg_color} on {bg_color}")

            if y < height - 1:
                output_text.append("\n")

        return output_text

    def watch_duration(self, time: float) -> None:
        if not self.is_mounted:
            return

        self._restart_countdown_timer()

    def watch_remaining_time(self, time: float) -> None:
        """Called when the remaining time attribute changes."""
        minutes, seconds = divmod(time, 60)
        self._cooldown_text = (
            f"{minutes:02.0f}:{seconds:02.0f}m" if minutes > 0 else f"{seconds:05.2f}s"
        )
        self.refresh()

    def _restart_countdown_timer(self) -> None:
        self._countdown_timer.resume()
        self._anchor_time = monotonic()

    def _update_duration(self, new_duration: float) -> None:
        self.duration = new_duration

    def _update_remaining_time(self) -> None:
        """Method to update the remaining time."""
        self.remaining_time = max(0, self.duration - (monotonic() - self._anchor_time))

        if self.remaining_time == 0:
            self._countdown_timer.pause()
