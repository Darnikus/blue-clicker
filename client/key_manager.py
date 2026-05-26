import asyncio
import logging
import random

from bluetooth_driver import BluetoothDriver

logger = logging.getLogger(__name__)


class KeyManager:
    def __init__(self, driver: BluetoothDriver) -> None:
        self._driver: BluetoothDriver = driver
        self._is_not_paused: bool = False
        self._is_running: bool = True

        self._key: str = "a"
        self._interval: int = 4

    async def start_sending(self) -> None:
        """Gives Textual breathing room to render before hammering the socket."""
        await asyncio.sleep(0.5)
        await self._send_message()

    def stop_sending(self) -> None:
        self._is_running = False
        self._driver.disconnect()

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state
        logger.info(f"--- SENDING {'RESUMED' if self._is_not_paused else 'PAUSED'} ---")

    async def _send_message(self) -> None:
        last_heartbeat = asyncio.get_event_loop().time()

        while self._is_running:
            if self._is_not_paused:
                if not await self._driver.send_data(self._key):
                    logger.exception("Could not send data. Waiting for next cycle...")
                    await asyncio.sleep(3)
                    continue

                # If you don't receive data, the script won't know the
                # socket is dead until the next .send() call fails.
                await asyncio.sleep(self._interval + self._get_random_human_reaction())

            elif asyncio.get_event_loop().time() - last_heartbeat > 5:
                logger.info("Sending heartbeat")
                await self._driver.send_data("\n")
                last_heartbeat = asyncio.get_event_loop().time()
                await asyncio.sleep(0.1)

            else:
                await asyncio.sleep(0.01)

        self._driver.disconnect()

    @staticmethod
    def _get_random_human_reaction() -> float:
        return random.randint(0, 200) / 1000
