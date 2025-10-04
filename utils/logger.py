
from loguru import logger
from pathlib import Path

class Logger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(str(self.path), rotation="5 MB", retention=10, serialize=True)

    def write_block(self, title: str, payload):
        logger.bind(kind="block").info({"title": title, "payload": payload})
