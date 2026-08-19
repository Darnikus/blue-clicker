import time
from dataclasses import dataclass, field


@dataclass(order=True)
class PrioritizedKey:
    """Represents a prioritized key added to a priority queue.

    Attributes:
        priority (int): Lower number means higher priority 0 = Emergency, 10 = Lowest.
        timestamp (float): Secondary sort if priorities match.
        key (str): Key to send.
    """

    priority: int
    timestamp: float = field(init=False)
    key: str = field(compare=False)

    def __post_init__(self):
        self.timestamp = time.time()
