
class TesterAgent:
    def __init__(self, client): self.client = client
    def run(self, code: str) -> str:
        return "print('tests for code len:', %d)" % len(code)
