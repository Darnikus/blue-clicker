import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from driver.bluetooth_driver import BluetoothDriver
from manager.key_task import KeyTask
from manager.preview_preset import PreviewPreset
from manager.prioritized_key import PrioritizedKey

logger = logging.getLogger(__name__)


class KeyManager:
    """Responsible for managing the state of key tasks.

    Attributes:
        _driver (BluetoothDriver): A driver that receives the produced keys for sending.
        _is_not_paused (bool): The flag that pauses keys transmission.
        _active_tasks (dict[str, KeyTask]): Dict of active key tasks.
        _is_running (bool): Tracks whether the consumer loop is currently running.
        _send_queue (asyncio.PriorityQueue): The queue for prioritized keys.
        _consumer_task (asyncio.Task | None): The consumer task that runs the consumer
            loop.
    """

    def __init__(self, driver: BluetoothDriver) -> None:
        self._driver: BluetoothDriver = driver

        self._is_not_paused: bool = False
        self._active_tasks: dict[str, KeyTask] = {}

        self._is_running: bool = False
        self._send_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._consumer_task: asyncio.Task | None = None

    @property
    def has_active_tasks(self) -> bool:
        """Verifies whether there is any ongoing task.

        Returns:
            bool: True if there is; False otherwise.
        """
        return bool(self._active_tasks)

    def add_key(
        self, key: str, interval: float, priority: int
    ) -> tuple[str, Callable[[Callable[[float], None]], None]]:
        """Adds a new key to the manager.

        Args:
            key (str): A key to send.
            interval (float): The time gap between key sends in seconds.
            priority (int): Indicate the importance of the key on a scale from 0 to 10,
                where 0 is the highest importance and 10 is the lowest.

        Returns:
            tuple[str, Callable[[Callable[[float], None]], None]]: Tuple of a key ID and
                its attachment for an observer to subscribe to.
        """
        key_task = KeyTask(self._send_queue, key, interval, priority)
        if self._is_not_paused:
            key_task.toggle_pause(self._is_not_paused)

        key_task.start()
        task_id = uuid.uuid4().hex[:16]
        self._active_tasks[task_id] = key_task
        return task_id, key_task.attach

    def edit_key(self, task_key: str, new_interval: float, new_priority: int) -> None:
        """Modifies the key's interval and priority.

        Args:
            task_key (str): A key ID.
            new_interval (float): The new interval in seconds.
            new_priority (int): The new priority.
        """
        key_task = self._active_tasks[task_key]
        key_task.interval = new_interval
        key_task.priority = new_priority

    def remove_key(self, task_id: str) -> None:
        """Removes the key from the manager.

        Args:
            task_id (str): A key ID.
        """
        key_task = self._active_tasks.pop(task_id)
        key_task.stop()

        logger.info(
            f"Removed key: {key_task.key} with interval: {key_task.interval} sec"
        )

    def get_file_preview(self, path: Path) -> PreviewPreset:
        """Loads a preview from the file.

        Args:
            path (Path): The path to the preset.

        Returns:
            PreviewPreset: "A preview extracted from a preset file.
        """
        with open(path) as file:
            data = json.load(file)

        return PreviewPreset(data["description"], data["keys"].values())

    async def load_preset_from_file(
        self, path: Path
    ) -> tuple[
        dict[str, dict[str, Any]], list[Callable[[Callable[[float], None]], None]]
    ]:
        """Load preset from a file.

        Args:
            path (Path): The path to the preset.

        Returns:
            tuple[dict, list]: A tuple containing keys and their associated callbacks
                from the file.
        """
        await self._cleanup_tasks()

        with open(path) as file:
            data = json.load(file)

        keys: dict[str, dict[str, Any]] = data["keys"]
        attach_callbacks: list[Callable[[Callable[[float], None]], None]] = []

        for key_id, key in keys.items():
            key_task = KeyTask(self._send_queue, **key)
            if self._is_not_paused:
                key_task.toggle_pause(self._is_not_paused)

            key_task.start()
            self._active_tasks[key_id] = key_task
            attach_callbacks.append(key_task.attach)

        return keys, attach_callbacks

    def save_keys_to_file(self, file_name: str, description: str | None) -> None:
        """Saves the current preset to a file.

        Args:
            file_name (str): A filename for a new preset.
            description (str | None): A purpose of a new preset.
        """
        json_profile = {
            "description": description,
            "keys": {
                key_id: key.to_dict() for key_id, key in self._active_tasks.items()
            },
        }
        path = Path(f"presets/{file_name}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(json_profile, file, indent=4)
        logger.info(f"Preset saved to '{file_name}.json'.")

    def start(self) -> None:
        """Starts the manager's duties."""
        self._is_running = True
        loop = asyncio.get_running_loop()
        self._consumer_task = loop.create_task(self._run_consumer_loop())

    async def shutdown(self) -> None:
        """Shutdowns the manager."""
        await self._cleanup_tasks()

        self._is_running = False
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()

        self._driver.disconnect()

    def toggle_pause(self, state: bool) -> None:
        """Pause or resume sending keys.

        Args:
            state (bool): True to resume; False to pause.
        """
        self._is_not_paused = state
        for key_task in self._active_tasks.values():
            key_task.toggle_pause(state)

        logger.info(f"--- SENDING {'RESUMED' if self._is_not_paused else 'PAUSED'} ---")

    def is_duplicate(self, check_key: str) -> bool:
        """Check if such key already exists

        Args:
            check_key (str): The suspected duplicate key.

        Returns:
            bool: True if the key appears more than once; False otherwise.
        """
        return any(task.key == check_key for task in self._active_tasks.values())

    def has_preset_files(self) -> bool:
        """Checks whether the preset directory exists and contains presets.

        Returns:
            bool: True if there is a preset directory containing presets; False
                otherwise.
        """
        directory = Path("presets")
        file_format = ".json"
        return directory.is_dir() and any(directory.glob(f"*{file_format}"))

    def file_exists(self, file_name: str) -> bool:
        """Checks if the preset file already exists

        Args:
            file_name (str): The preset's file name.

        Returns:
            bool: True if the preset already exists; False otherwise.
        """
        return Path(f"presets/{file_name}.json").exists()

    async def _cleanup_tasks(self) -> None:
        """Cancel all tasks and clean the consumer queue"""
        active_producers = [task.stop() for task in self._active_tasks.values()]
        active_producers = [task for task in active_producers if task is not None]
        if active_producers:
            # Wait untill all tasks have been stopped
            await asyncio.gather(*active_producers, return_exceptions=True)

        self._active_tasks.clear()

        while not self._send_queue.empty():
            try:
                self._send_queue.get_nowait()
                self._send_queue.task_done()
            except asyncio.QueueEmpty:
                break

    async def _run_consumer_loop(self) -> None:
        """The single consumer worker that reads from the priority queue
        and sends data sequentially to the driver"""

        try:
            while self._is_running:
                # Blocks cleanly until a key drops into the queue
                item: PrioritizedKey = await self._send_queue.get()

                if self._is_not_paused:
                    logger.info(
                        f"Consumer sending: '{item.key}'"
                        + f" (Priority: '{item.priority}')."
                    )
                    if not await self._driver.send_data(
                        f"ACTION:PRESS|PAYLOAD:{item.key}"
                    ):
                        logger.error(f"Driver failed to send key: '{item.key}'.")

                        # Attempt to resend a key with high priority again
                        if item.priority <= 3:
                            logger.info(f"Resending high priority key: '{item.key}'.")
                            await self._driver.send_data(item.key)
                else:
                    logger.info(f"Dropped item '{item.key}' because manager is paused.")

                self._send_queue.task_done()

                # Tiny cooldown between consecutive sends
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass
