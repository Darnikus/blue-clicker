import asyncio
import logging
import random

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Log

from bluetooth_driver import BluetoothDriver

logger = logging.getLogger(__name__)


class _TextualLogHandler(logging.Handler):
    def __init__(self, log_widget: Log) -> None:
        super().__init__()

        self._log_widget: Log = log_widget

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        self._log_widget.app.call_next(self._log_widget.write_line, message)


class BlueClickerApp(App):
    def __init__(self, driver: BluetoothDriver) -> None:
        super().__init__()

        self._is_running: bool = True
        self._sending_flag: bool = True
        self._blu_driver: BluetoothDriver = driver

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(auto_scroll=True, id="log")
        yield Footer()

    def on_mount(self) -> None:
        # Logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        log_widget: Log = self.query_one("#log", Log)
        handler = _TextualLogHandler(log_widget)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        root_logger.addHandler(handler)

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
            if self._sending_flag:
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
