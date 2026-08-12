import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class InvalidActionError(ValueError):
    """Raised when the action string is unrecognized."""

    def __init__(self, *args: object, invalid_action=None) -> None:
        super().__init__(*args)
        self.invalid_action = invalid_action


class Action(StrEnum):
    HOLD = "HOLD"
    PRESS = "PRESS"
    RELEASE = "RELEASE"

    @classmethod
    def _missing_(cls, value):
        valid_options = ", ".join([repr(a.value) for a in cls])
        raise InvalidActionError(
            f"'{value}' is not a valid {cls.__name__}. Choose from [{valid_options}]",
            invalid_action=value,
        )


@dataclass(frozen=True)
class ProtocolMessage:
    action: Action
    payload: str = ""

    def serialize(self) -> str:
        """Encodes the message into the custom format"""
        return f"ACTION:{self.action}|PAYLOAD:{self.payload}"

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        """Parses message from the request into a ProtocolMessage object."""
        decoded = data.decode("utf-8").strip()

        try:
            packet = json.loads(decoded)
            action: str = packet.get("action")
            payload = packet.get("payload")

            return cls(action=Action(action.upper()), payload=payload)

        # Let InvalidActionError raise
        except InvalidActionError:
            raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Couldn't deserialize message: {decoded}") from e
