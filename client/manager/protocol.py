import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Action(StrEnum):
    HOLD = "HOLD"
    PRESS = "PRESS"
    RELEASE = "RELEASE"


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
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Couldn't deserialize message: {decoded}") from e
