import logging
from logging import LoggerAdapter, getLogger

from rich.logging import RichHandler


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "id") or record.id is None:
            record.id = ""

        return super().format(record)

    def formatMessage(self, record):
        message = super().formatMessage(record)
        return message.replace("[ ]", "").replace("[]", "")


def make_logger(name: str, id: int | None = None, level=logging.DEBUG) -> LoggerAdapter:
    logger = getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = RichHandler(rich_tracebacks=True, markup=True)
        formatter = CustomFormatter("[magenta]%(name)s[/magenta][%(id)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return LoggerAdapter(logger, {"id": id})
