SCHEMA = '{"sprint_title": str, "sprint_goal": str, "weeks": [{"week_number": int, "tasks": [{"task_id": str, "title": str, "description": str, "agent_type": str, "dependencies": [str], "estimated_hours": int}]}]}'

class ArchitectAgent:
    def __init__(self, client):
        self.client = client

    def run(self, directive: str) -> dict:
        system = ("You are a software architect. Return ONLY JSON plan. "
                  "agent_type must be one of: coder, tester, integrator.")
        prompt = f"Directive:\n{directive}\nNow output strict JSON."
        r = self.client.call_json("architect", prompt, system, schema_hint=SCHEMA)
        if r.get("json"):
            return r["json"]
        return {
            "sprint_title": "Fallback Sprint",
            "sprint_goal": directive[:100],
            "weeks": [{"week_number": 1, "tasks": [{"task_id": "T-1","title":"Scaffold","description":"Create a simple module","agent_type":"coder","dependencies":[],"estimated_hours":2}]}]
        }
