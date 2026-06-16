import time
from dataclasses import dataclass, field


@dataclass(order=True)
class PrioritizedKey:
    priority: int  # Lower number means higher priority 0 = Emergency, 10 = Lowest
    timestamp: float = field(init=False)  # Secondary sort if priorities match
    key: str = field(compare=False)

    def __post_init__(self):
        self.timestamp = time.time()
