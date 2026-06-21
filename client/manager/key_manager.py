import asyncio
import logging

from driver.bluetooth_driver import BluetoothDriver
from manager.key_task import KeyTask
from manager.prioritized_key import PrioritizedKey

logger = logging.getLogger(__name__)


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

    def edit_key(self, task_key: str, new_interval: float, new_priority: int) -> None:
        key_task = self._active_tasks[task_key]
        key_task.interval = new_interval
        key_task.priority = new_priority

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
                # todo change to 0.1
                await asyncio.sleep(0.02)

        except asyncio.CancelledError:
            pass
