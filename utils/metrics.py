
import json, time
from pathlib import Path

class Metrics:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, item: dict):
        item = dict(item)
        item["ts"] = time.time()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
