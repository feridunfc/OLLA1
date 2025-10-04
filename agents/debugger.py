class DebuggerAgent:
    def __init__(self, client):
        self.client = client

    def run(self, code: str, error: str, context: dict | None = None) -> str:
        system = "You are a Python debugging expert. Return ONLY corrected Python code."
        ctx = f"Context: {context}" if context else ""
        prompt = f"{ctx}\\nFix code based on error below.\\nError:\\n{error}\\nCode:\\n{code}"
        r = self.client.call("debugger", prompt, system, num_predict=1000, temperature=0.2)
        return r["text"].strip()
