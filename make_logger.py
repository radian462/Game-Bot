import logging
from logging import getLogger

def make_logger(name: str, level=logging.DEBUG) -> getLogger:
    logger = getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s:%(name)s] %(message)s - %(asctime)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger