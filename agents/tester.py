class TesterAgent:
    def __init__(self, client):
        self.client = client

    def run(self, code: str, context: dict | None = None) -> str:
        system = "You are a QA writing pytest. Return ONLY Python code (tests)."
        ctx = f"Context: {context}" if context else ""
        prompt = f"{ctx}\\nWrite pytest tests for this code:\\n{code}"
        r = self.client.call("tester", prompt, system, num_predict=900, temperature=0.2)
        return r["text"].strip()
