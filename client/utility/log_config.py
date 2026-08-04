import logging

from textual.widgets import RichLog

__all__ = ["initialize_logging", "link_textual_ui"]


class _TextualLogHandler(logging.Handler):
    def __init__(self, log_widget: RichLog) -> None:
        super().__init__()

        self._log_widget: RichLog = log_widget

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        self._log_widget.app.call_next(self._log_widget.write, message)


def initialize_logging() -> None:
    # Logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)


def link_textual_ui(log_widget: RichLog):
    handler = _TextualLogHandler(log_widget)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] (%(module)s) -> %(message)s"
    )  # Old format "%(asctime)s - %(levelname)s - %(message)s"
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
