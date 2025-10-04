import json
class IntegratorAgent:
    def __init__(self, client):
        self.client = client

    def run(self, results: dict) -> dict:
        system = "You are an integrator. Return JSON with pr_url, summary, next_steps[]."
        prompt = f"Summarize results: {json.dumps(results)[:4000]}"
        r = self.client.call_json("integrator", prompt, system)
        return r.get("json") or {"pr_url":"", "summary":"local summary", "next_steps":["run app","manual review"]}
