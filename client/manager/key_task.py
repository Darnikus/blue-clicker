import asyncio
import logging
import random
from collections.abc import Callable

from manager.prioritized_key import PrioritizedKey

logger = logging.getLogger(__name__)


class KeyTask:
    """Custom task to press a key at a designated interval.

    Attributes:
        key (str): Key to send.
        _key_queue (asyncio.PriorityQueue[PrioritizedKey]): The queue for putting
            prioritized keys.
        _interval (float): The raw interval between key sends in seconds.
        _priority (int): The internal key's priority level.
        _task (asyncio.Task | None): The task object.
        _interval_change_event (asyncio.Event): Triggered when the interval changes,
            allowing the task to wake up earlier.
        _total_sleep (float): The raw value that reflects both the interval and a human
            reaction.
        _is_not_paused (bool): The flag that pauses key transmission.
        _is_running (bool): Tracks whether the main processing loop is currently
            running.
        _observer (Callable[[float], None] | None): The link to the observer to notify
            about timeout changes.
    """

    def __init__(
        self, key_queue: asyncio.PriorityQueue, key: str, interval: float, priority: int
    ) -> None:
        self._key_queue: asyncio.PriorityQueue[PrioritizedKey] = key_queue
        self.key: str = key
        self._interval: float = interval
        self._priority: int = priority

        self._task: asyncio.Task | None = None
        self._interval_change_event: asyncio.Event = asyncio.Event()
        self._total_sleep: float = 0.0

        self._is_not_paused: bool = False
        self._is_running: bool = False

        self._observer: Callable[[float], None] | None = None

    @property
    def interval(self) -> float:
        """float: The time gap between key sends in seconds."""
        return self._interval

    @interval.setter
    def interval(self, new_interval: float) -> None:
        """Sets the interval and the _interval_change_event when the interval changes.

        Args:
            new_interval (float): The interval in seconds.
        """
        if self._interval != new_interval:
            logger.info(
                f"[{self.key}] Changing interval from {self.interval}s"
                + f" to {new_interval}s."
            )
            self._interval = new_interval
            self._interval_change_event.set()

    @property
    def priority(self) -> int:
        """int: The key's priority level from 0 to 10."""
        return self._priority

    @priority.setter
    def priority(self, new_priority: int) -> None:
        """Sets the key's priority level and ensures it stays within defined bounds.

        Args:
            new_priority (int): The priority level.

        Raises:
            ValueError: If the priority level value is outside the range of 0 to 10.
        """
        if new_priority < 0 or new_priority > 10:
            raise ValueError("Priority cannot be smaller than 0 and bigger than 10")
        self._priority = new_priority

    @property
    def total_sleep(self) -> float:
        """float: The time when the task will wake up next."""
        return self._total_sleep

    @total_sleep.setter
    def total_sleep(self, new_value: float) -> None:
        """Sets the time at which the task will wake up.

        Args:
            new_value (float): The wake up time.
        """
        if self.total_sleep != new_value:
            self._total_sleep = new_value
            self._notify_observer()

    def start(self) -> None:
        """Starts the task."""
        if self._task and not self._task.done():
            logger.error(f"Task for key: {self.key} is already running.")
            return

        self._is_running = True
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run_loop())
        logger.info(f"Started loop task for key: {self.key}")

    def stop(self) -> asyncio.Task | None:
        """Stops the task.

        Returns:
            asyncio.Task | None: The task object or None if the task has already
                stopped.
        """
        self._is_running = False

        current_task = self._task if (self._task and not self._task.done()) else None
        if current_task:
            current_task.cancel()

        self._task = None
        return current_task

    def toggle_pause(self, state: bool) -> None:
        """Pause or resume key sending.

        Args:
            state (bool): True to resume; False to pause.
        """
        self._is_not_paused = state

    def to_dict(self) -> dict[str, str | float | int]:
        """Stores the KeyTask properties into a dictionary.

        Returns:
            dict[str, str | float | int]: Dict of key, interval, and priority.
        """
        return {"key": self.key, "interval": self.interval, "priority": self.priority}

    def attach(self, callback: Callable[[float], None]) -> None:
        """Attach an observer to the subject.

        Args:
            callback (Callable[[float], None]): The attachment to the observer.
        """
        self._observer = callback

    def _notify_observer(self) -> None:
        """Notify the observer about the changed timeout."""
        if self._observer is not None:
            self._observer(self.total_sleep)

    async def _run_loop(self) -> None:
        """The main loop of the task."""
        try:
            while self._is_running:
                if self._is_not_paused:
                    if self.key is None or self.interval is None:
                        logger.exception("Key and interval are unconfigured.")
                        continue

                    item = PrioritizedKey(priority=self.priority, key=self.key)
                    await self._key_queue.put(item)

                    self._interval_change_event.clear()
                    try:
                        self.total_sleep = (
                            self.interval + self._get_random_human_reaction()
                        )

                        # If you don't receive data, the script won't know the
                        # socket is dead until the next .send() call fails.
                        async with asyncio.timeout(self.total_sleep):
                            await self._interval_change_event.wait()
                            logger.info(
                                f"[{self.key}] Interval change detected."
                                + " Waking up to apply new setting."
                            )
                    except TimeoutError:
                        pass

                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"Loop for key: {self.key} was canceled.")

    @staticmethod
    def _get_random_human_reaction() -> float:
        """Replicates human reaction speed.

        Returns:
            float: The random human reaction time ranges from 0 to 0.2 seconds.
        """
        return random.randint(0, 200) / 1000
