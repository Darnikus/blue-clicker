from collections.abc import Callable
from time import monotonic

from rich.console import RenderableType
from rich.text import Text
from textual.color import Gradient
from textual.reactive import reactive
from textual.widgets import Static


class KeyCooldown(Static):
    """Custom widget that displays the countdown to the next key press.

    Attributes:
        duration (reactive[float]): Duration of the widget's animation.
        remaining_time (reactive[float]): Remaining time until the widget's animation
            finishes.
        is_paused (reactive[bool]): The flag that pauses the widget's animation.
        key_id (str): ID from DataTable for comparison.
        _key (str): A key to show.
        _anchor_time (float): An anchor for calculating remaining time.
        _gradient (Gradient): Colors used to render the widget.
        _attach_callable (Callable[[Callable[[float], None]], None]) -> None): The link
            to subscribe to duration updates.
    """

    DEFAULT_CSS = """
        KeyCooldown {
            color: white;
            background: black;
            text-style: bold;
        }
    """

    duration = reactive(0.0)
    remaining_time = reactive(0.0)
    is_paused: reactive[bool] = reactive(True)

    def __init__(
        self,
        key_id: str,
        key: str,
        duration: float,
        paused_state: bool,
        attach_callable: Callable[[Callable[[float], None]], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.key_id = key_id
        self._key: str = key
        self.duration = duration
        self._anchor_time = monotonic()

        self._gradient = Gradient.from_colors("dimgray", "darkorange", "red")

        self.is_paused = not paused_state  # Maybe will rework flags later

        self._attach_callable: Callable[[Callable[[float], None]], None] = (
            attach_callable
        )

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self._attach_callable(
            self._update_duration
        )  # Subscribe here, because i need to wait for next notify if do it in init
        self._countdown_timer = self.set_interval(
            1 / 100, self._update_remaining_time, pause=self.is_paused
        )  # maybe change interval to 1 / 60

    def render(self) -> RenderableType:
        width = self.size.width or 40
        height = self.size.height or 3

        progress_ratio = 1 - (
            self.remaining_time / self.duration
        )  # line goes from left to right
        fill_width = int(width * progress_ratio)

        message = f"{self._key} - {'Paused' if self.is_paused else self._cooldown_text}"
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
        """Called when the duration attribute changes.

        Args:
            time (float): New duration value.
        """
        if not self.is_mounted:
            return

        self._restart_countdown_timer()

    def watch_is_paused(self, state: bool) -> None:
        """Pauses and resumes the widget's animation. Called when the duration attribute
        changes.

        Args:
            state (bool): True to pause; False to resume.
        """
        if self.is_mounted and state:  # Seems like i need to change sending_flag
            self._countdown_timer.pause()
            self.refresh()
        elif self.is_mounted and not state:
            self._countdown_timer.resume()
            self.refresh()

    def watch_remaining_time(self, time: float) -> None:
        """Called when the remaining time attribute changes.

        Args:
            time (float): New remaining time value.
        """
        minutes, seconds = divmod(time, 60)
        self._cooldown_text = (
            f"{minutes:02.0f}:{seconds:02.0f}m" if minutes > 0 else f"{seconds:05.2f}s"
        )
        self.refresh()

    def _restart_countdown_timer(self) -> None:
        """Restarts the animation."""
        self._countdown_timer.resume()
        self._anchor_time = monotonic()

    def _update_duration(self, new_duration: float) -> None:
        """Subscribe method to receive duration updates.

        Args:
            new_duration (float): Received new duration.
        """
        self.duration = new_duration

    def _update_remaining_time(self) -> None:
        """Method to update the remaining time."""
        self.remaining_time = max(0, self.duration - (monotonic() - self._anchor_time))

        if self.remaining_time == 0:
            self._countdown_timer.pause()
