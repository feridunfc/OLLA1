
class CoderAgent:
    def __init__(self, client): self.client = client
    def run(self, desc: str) -> str:
        return "print('code generated for: ' + str(%r))" % desc
