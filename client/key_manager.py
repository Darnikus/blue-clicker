import asyncio
import logging
import random

from bluetooth_driver import BluetoothDriver

logger = logging.getLogger(__name__)


class KeyTask:
    def __init__(self, key: str, interval: float, driver: BluetoothDriver) -> None:
        self.key: str = key
        self.interval: float = interval

        self.task: asyncio.Task | None = None

        self._is_not_paused: bool = False
        self._is_running: bool = False

        self._driver = driver

    def start(self) -> None:
        if self.task and not self.task.done():
            logger.error(f"Task for key: {self.key} is already running.")
            return

        self._is_running = True
        loop = asyncio.get_running_loop()
        self.task = loop.create_task(self._run_loop())
        logger.info(f"Started loop task for key: {self.key}")

    def stop(self) -> None:
        self._is_running = False
        if self.task and not self.task.done():
            self.task.cancel()

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state

    async def _run_loop(self) -> None:
        try:
            while self._is_running:
                if self._is_not_paused:
                    if self.key is None or self.interval is None:
                        logger.exception("Key and interval are unconfigured.")
                        continue

                    if not await self._driver.send_data(self.key):
                        logger.exception(
                            "Could not send data. Waiting for next cycle..."
                        )
                        await asyncio.sleep(3)
                        continue

                    # If you don't receive data, the script won't know the
                    # socket is dead until the next .send() call fails.
                    await asyncio.sleep(
                        self.interval + self._get_random_human_reaction()
                    )

                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"Loop for key: {self.key} was canceled.")

    @staticmethod
    def _get_random_human_reaction() -> float:
        return random.randint(0, 200) / 1000


class KeyManager:
    def __init__(self, driver: BluetoothDriver) -> None:
        self._driver: BluetoothDriver = driver
        self._is_not_paused: bool = False
        self._is_running: bool = True

        self._key: str | None = None
        self._interval: float | None = None

        self._active_tasks: dict[str, KeyTask] = {}

    @property
    def key(self) -> str | None:
        return self._key

    @key.setter
    def key(self, new_key: str | None):
        self._key = new_key

    @property
    def interval(self) -> float | None:
        return self._interval

    @interval.setter
    def interval(self, new_interval: float | None):
        self._interval = new_interval

    @property
    def has_active_tasks(self) -> bool:
        """Returns True if there is any active task"""
        return bool(self._active_tasks)

    def add_key(self, task_id: str, key: str, interval: float) -> None:
        key_task = KeyTask(key, interval, self._driver)
        if self._is_not_paused:
            key_task.toggle_pause(self._is_not_paused)

        key_task.start()
        self._active_tasks[task_id] = key_task

    def remove_key(self, task_id: str) -> None:
        key_task = self._active_tasks.pop(task_id)
        key_task.stop()

        logger.info(
            f"Removed key: {key_task.key} "
            + f"with interval: {key_task.interval} sec"
        )

    def shutdown(self) -> None:
        self._is_running = False

        for key_task in self._active_tasks.values():
            key_task.stop()

        self._driver.disconnect()

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state
        for key_task in self._active_tasks.values():
            key_task.toggle_pause(state)

        logger.info(f"--- SENDING {'RESUMED' if self._is_not_paused else 'PAUSED'} ---")
