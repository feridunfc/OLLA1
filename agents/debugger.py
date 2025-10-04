
class DebuggerAgent:
    def __init__(self, client): self.client = client
    def run(self, code: str, error_output: str) -> str:
        return code + "\n# patched"
