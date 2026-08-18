"""Managing logger setup and its handler to display logs in the App's log widget."""

import logging
from contextvars import ContextVar

from textual.widgets import RichLog

active_log_widget: ContextVar[RichLog | None] = ContextVar(
    "active_log_widget", default=None
)
"""The context variable that contains a log widget on the current screen."""


class _TextualLogHandler(logging.Handler):
    """Handles incoming logs from the logger and forwards them to an active log widget.

    Attributes:
        _level_colors (dict[str, str]): Colors for different log levels.
    """

    def __init__(self) -> None:
        super().__init__()

        self._level_colors = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
        }

    def emit(self, record: logging.LogRecord) -> None:
        log_widget = active_log_widget.get()
        if log_widget and log_widget.is_mounted:
            color = self._level_colors.get(record.levelname, "white")
            record.levelname = f"[{color}][{record.levelname}][/{color}]"
            message = self.format(record)

            log_widget.app.call_next(log_widget.write, message)


def initialize_logging() -> None:
    """Initialize the project logger."""
    # Logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = _TextualLogHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s (%(module)s) -> %(message)s"
    )  # Old format "%(asctime)s - %(levelname)s - %(message)s"
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
