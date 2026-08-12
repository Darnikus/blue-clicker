import logging
from contextvars import ContextVar

from textual.widgets import RichLog

__all__ = ["initialize_logging"]

active_log_widget: ContextVar[RichLog | None] = ContextVar(
    "active_log_widget", default=None
)


class _TextualLogHandler(logging.Handler):
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
    # Logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = _TextualLogHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s (%(module)s) -> %(message)s"
    )  # Old format "%(asctime)s - %(levelname)s - %(message)s"
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
