from time import monotonic

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Static


class KeyCooldown(Static):
    duration = reactive(0.0)
    remaining_time = reactive(0.0)

    def __init__(self, key: str, interval: float, **kwargs) -> None:
        super().__init__(**kwargs)

        self._key: str = key
        self.duration = interval
        self._anchor_time = monotonic()

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self._countdown_timer = self.set_interval(1 / 200, self._update_remaining_time)

    def watch_remaining_time(self, time: float) -> None:
        """Called when the remaining time attribute changes."""
        minutes, seconds = divmod(time, 60)
        time_to_print = (
            f"{minutes:02.0f}:{seconds:02.0f}m" if minutes > 0 else f"{seconds:05.2f}s"
        )
        self.update(f"{self._key} - {time_to_print}")

    def _update_remaining_time(self) -> None:
        """Method to update the remaining time."""
        self.remaining_time = max(0, self.duration - (monotonic() - self._anchor_time))

        if self.remaining_time == 0:
            self._countdown_timer.pause()
            self._anchor_time = monotonic()
            self._countdown_timer.resume()


class DemoApp(App):
    CSS_PATH = "test.tcss"

    def compose(self) -> ComposeResult:
        yield KeyCooldown("D", 10)


if __name__ == "__main__":
    app = DemoApp()
    app.run()
