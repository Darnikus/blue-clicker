from dataclasses import dataclass


@dataclass
class PreviewPreset:
    """Represents a preview extracted from a preset file.

    Attributes:
        description (str): The explanation of a preset's intended purpose.
        keys (list[dict[str, str | float | int]]): The list of keys from a preset.
    """

    description: str
    keys: list[dict[str, str | float | int]]
