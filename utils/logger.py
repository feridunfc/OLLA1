import json, time
class Logger:
    def __init__(self, path: str):
        self.path = path
    def write_block(self, title: str, payload):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {title} @ {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
            if isinstance(payload, str):
                f.write(payload + "\n")
            else:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
