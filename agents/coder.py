import re
def _extract_code(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            inner = parts[i]
            inner = inner.split("\n", 1)[-1] if "\n" in inner else inner
            if inner.strip():
                return inner.strip()
        return parts[-1].strip()
    lines = text.splitlines()
    for idx, ln in enumerate(lines):
        if re.search(r'^(from\\s+\\w+\\s+import|import\\s+\\w+|def\\s+\\w+|class\\s+\\w+|app\\s*=\\s*FastAPI\\(\\))', ln.strip()):
            return "\\n".join(lines[idx:])
    return text

class CoderAgent:
    def __init__(self, client):
        self.client = client

    def run(self, task_description: str, context: dict | None = None) -> str:
        system = "You are a Python expert. Return ONLY valid Python code. No markdown."
        ctx = f"Context: {context}" if context else ""
        prompt = f"{ctx}\\nTask: {task_description}\\nReturn ONLY code."
        r = self.client.call("coder", prompt, system, num_predict=1200, temperature=0.2)
        return _extract_code(r["text"])
