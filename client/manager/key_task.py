import asyncio
import logging
import random

from manager.prioritized_key import PrioritizedKey

logger = logging.getLogger(__name__)


class KeyTask:
    def __init__(
        self, key_queue: asyncio.PriorityQueue, key: str, interval: float, priority: int
    ) -> None:
        self._key_queue: asyncio.PriorityQueue[PrioritizedKey] = key_queue
        self.key: str = key
        self._interval: float = interval
        self._priority: int = priority

        self._task: asyncio.Task | None = None
        self._interval_change_event: asyncio.Event = asyncio.Event()

        self._is_not_paused: bool = False
        self._is_running: bool = False

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, new_interval: float) -> None:
        if self._interval != new_interval:
            logger.info(
                f"[{self.key}] Changing interval from {self.interval}s"
                + f" to {new_interval}s."
            )
            self._interval = new_interval
            self._interval_change_event.set()

    @property
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, new_priority: int) -> None:
        if new_priority < 1 or new_priority > 10:
            raise ValueError("Priority cannot be smaller than 1 and bigger than 10")
        self._priority = new_priority

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
        self._task = None

    def toggle_pause(self, state: bool) -> None:
        self._is_not_paused = state

    def to_dict(self) -> dict[str, str | float | int]:
        """Return dict with key, interval and priority."""
        return {"key": self.key, "interval": self.interval, "priority": self.priority}

    async def _run_loop(self) -> None:
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
                        total_sleep = self.interval + self._get_random_human_reaction()

                        # If you don't receive data, the script won't know the
                        # socket is dead until the next .send() call fails.
                        async with asyncio.timeout(total_sleep):
                            await self._interval_change_event.wait()
                            logger.info(
                                f"[{self.key}] Interval change detected."
                                + " Waking up to apply new setting."
                            )
                    except asyncio.TimeoutError:
                        pass

                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"Loop for key: {self.key} was canceled.")

    @staticmethod
    def _get_random_human_reaction() -> float:
        return random.randint(0, 200) / 1000
