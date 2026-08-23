import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class InvalidActionError(ValueError):
    """Raised when the action string is unrecognized.

    Attributes:
        invalid_action (Unknown | None): Invalid action received from the API.
    """

    def __init__(self, *args: object, invalid_action=None) -> None:
        super().__init__(*args)
        self.invalid_action = invalid_action


class Action(StrEnum):
    """Defines the key-press actions available to users in the program."""

    HOLD = "HOLD"
    """Hold a key."""
    PRESS = "PRESS"
    """Press a key."""
    RELEASE = "RELEASE"
    """Release a held key."""

    @classmethod
    def _missing_(cls, value):
        """Handles lookups for actions that aren't present in the existing set.

        Args:
            value (object): The raw value provided for the enum lookup.

        Raises:
            InvalidActionError: If the provided value does not match any valid action.
        """
        valid_options = ", ".join([repr(a.value) for a in cls])
        raise InvalidActionError(
            f"'{value}' is not a valid {cls.__name__}. Choose from [{valid_options}]",
            invalid_action=value,
        )


@dataclass(frozen=True)
class ProtocolMessage:
    """Represents a message to send to the driver.

    Attributes:
        action (Action): Required action to be performed with a payload.
        payload (str): Message to be sent.
    """

    action: Action
    payload: str = ""

    def serialize(self) -> str:
        """Serialize the message into the custom format.

        Returns:
            str: Message prepared for sending to the driver.
        """
        return f"ACTION:{self.action}|PAYLOAD:{self.payload}"

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        """Parses message from the request into a ProtocolMessage object.

        Args:
            data (bytes): Message encoded in UTF-8.

        Raises:
            InvalidActionError: If a provided action is invalid.
            ValueError: If a message couldn't be deserialized.

        Returns:
            Self: ProtocolMessage object.
        """
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
