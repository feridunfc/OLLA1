import json, time
class Metrics:
    def __init__(self, path: str):
        self.path = path
    def write(self, obj: dict):
        obj = dict(obj); obj["ts"]=time.time()
        with open(self.path,"a",encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False)+"\n")
