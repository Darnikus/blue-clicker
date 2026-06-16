import asyncio
import logging
import random

from bluetooth_driver import BluetoothDriver
from prioritized_key import PrioritizedKey

logger = logging.getLogger(__name__)


class KeyTask:
    def __init__(
        self, key_queue: asyncio.PriorityQueue, key: str, interval: float, priority: int
    ) -> None:
        self._key_queue: asyncio.PriorityQueue[PrioritizedKey] = key_queue
        self.key: str = key
        self.interval: float = interval
        self._priority: int = priority

        self._task: asyncio.Task | None = None

        self._is_not_paused: bool = False
        self._is_running: bool = False

    def start(self) -> None:
        if self._task and not self._task.done():
            logger.error(f"Task for key: {self.key} is already running.")
            return

        self._is_running = True
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run_loop())
        logger.info(f"Started loop task for key: {self.key}")

    def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state

    async def _run_loop(self) -> None:
        try:
            while self._is_running:
                if self._is_not_paused:
                    if self.key is None or self.interval is None:
                        logger.exception("Key and interval are unconfigured.")
                        continue

                    item = PrioritizedKey(priority=self._priority, key=self.key)
                    await self._key_queue.put(item)

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
        self._active_tasks: dict[str, KeyTask] = {}

        self._is_running: bool = False
        self._send_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._consumer_task: asyncio.Task | None = None

    @property
    def has_active_tasks(self) -> bool:
        """Returns True if there is any active task"""
        return bool(self._active_tasks)

    def add_key(self, task_id: str, key: str, interval: float, priority: int) -> None:
        key_task = KeyTask(self._send_queue, key, interval, priority)
        if self._is_not_paused:
            key_task.toggle_pause(self._is_not_paused)

        key_task.start()
        self._active_tasks[task_id] = key_task

    def remove_key(self, task_id: str) -> None:
        key_task = self._active_tasks.pop(task_id)
        key_task.stop()

        logger.info(
            f"Removed key: {key_task.key} with interval: {key_task.interval} sec"
        )

    def start(self) -> None:
        self._is_running = True
        loop = asyncio.get_running_loop()
        self._consumer_task = loop.create_task(self._run_consumer_loop())

    def shutdown(self) -> None:
        for key_task in self._active_tasks.values():
            key_task.stop()

        self._is_running = False
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()

        self._driver.disconnect()

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state
        for key_task in self._active_tasks.values():
            key_task.toggle_pause(state)

        logger.info(f"--- SENDING {'RESUMED' if self._is_not_paused else 'PAUSED'} ---")

    def is_duplicate(self, check_key: str) -> bool:
        """Check if such key already exists"""
        return any(task.key == check_key for task in self._active_tasks.values())

    async def _run_consumer_loop(self) -> None:
        """The single consumer worker that reads from the priority queue
        and sends data seuentially to the driver"""

        try:
            while self._is_running:
                # Blocks cleanly until a key drops into the queue
                item: PrioritizedKey = await self._send_queue.get()

                if self._is_not_paused:
                    logger.info(
                        f"Consumer sending: '{item.key}'"
                        + f" (Priority: '{item.priority}')."
                    )
                    if not await self._driver.send_data(item.key):
                        logger.error(f"Driver failed to send key {item.key}.")
                else:
                    logger.info(f"Dropped item '{item.key}' because manager is paused.")

                self._send_queue.task_done()

                # Tiny cooldown between consecutive sends
                await asyncio.sleep(0.02)

        except asyncio.CancelledError:
            pass
