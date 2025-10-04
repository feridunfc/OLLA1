
class IntegratorAgent:
    def __init__(self, client): self.client = client
    def run(self, results: dict) -> dict:
        return {"pr_url":"N/A-local","summary":"local simulation","next_steps":["manual review"]}
