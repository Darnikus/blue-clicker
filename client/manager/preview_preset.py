from dataclasses import dataclass


@dataclass
class PreviewPreset:
    description: str
    keys: list[dict[str, str | float | int]]
