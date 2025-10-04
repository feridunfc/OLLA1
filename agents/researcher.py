class ResearcherAgent:
    def __init__(self, client):
        self.client = client

    def run(self, goal: str) -> dict:
        system = ("You are a senior research analyst. "
                  "Respond ONLY in JSON keys: goals(list), assumptions(list), risks(list), open_questions(list), tech_stack(list), complexity(low|medium|high).")
        prompt = f"Goal: {goal}"
        r = self.client.call_json("researcher", prompt, system)
        return r.get("json") or {"goals":[goal],"assumptions":[],"risks":[],"open_questions":[],"tech_stack":[],"complexity":"medium"}
