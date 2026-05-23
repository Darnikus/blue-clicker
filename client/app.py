import asyncio
import logging
import random

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Footer, Header, Log

from bluetooth_driver import BluetoothDriver
from log_config import link_textual_ui

logger = logging.getLogger(__name__)


class BlueClickerApp(App):
    BINDINGS = [
        ("p", "toggle_pause", "Pause sending"),
        ("p", "toggle_resume", "Resume sending"),
    ]

    def __init__(self, driver: BluetoothDriver) -> None:
        super().__init__()

        self._is_running: bool = True
        self._blu_driver: BluetoothDriver = driver

    sending_flag: reactive[bool] = reactive(False, bindings=True)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(auto_scroll=True, id="log")
        yield Footer()

    def on_mount(self) -> None:
        log_widget: Log = self.query_one("#log", Log)
        link_textual_ui(log_widget)

        self.background_task = self.run_worker(self._secure_send_startup())

    async def _secure_send_startup(self) -> None:
        """Gives Textual breathing room to render before hammering the socket."""
        await asyncio.sleep(0.5)
        await self._send_message()

    def on_unmount(self) -> None:
        logger.info("App shutting down. Signaling background tasks to stop...")

        self._is_running = False
        self._blu_driver.disconnect()
        self.background_task.cancel()

    async def _send_message(self) -> None:
        last_heartbeat = asyncio.get_event_loop().time()

        while self._is_running:
            message = "a"
            if self.sending_flag:
                if not await self._blu_driver.send_data(message):
                    logger.exception("Could not send data. Waiting for next cycle...")
                    await asyncio.sleep(3)
                    continue

                # If you don't receive data, the script won't know the
                # socket is dead until the next .send() call fails.
                await asyncio.sleep(4 + random.randint(0, 200) / 1000)

            elif asyncio.get_event_loop().time() - last_heartbeat > 5:
                logger.info("Sending heartbeat")
                await self._blu_driver.send_data("\n")
                last_heartbeat = asyncio.get_event_loop().time()
                await asyncio.sleep(0.1)

            else:
                await asyncio.sleep(0.01)

        self._blu_driver.disconnect()

    def action_toggle_pause(self) -> None:
        """An action to pause sending."""
        self.sending_flag = False
        logger.info("--- SENDING PAUSED ---")

    def action_toggle_resume(self) -> None:
        """An action to resume sending."""
        self.sending_flag = True
        logger.info("--- SENDING RESUMED ---")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "toggle_pause" and not self.sending_flag:
            return False

        if action == "toggle_resume" and self.sending_flag:
            return False

        return True
