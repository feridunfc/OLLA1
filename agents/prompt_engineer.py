class PromptEngineerAgent:
    def __init__(self, client):
        self.client = client

    def craft_for_architect(self, research: dict) -> str:
        system = "You are a prompt engineer. Output a plain directive (no markdown) for architect to create a JSON sprint plan."
        prompt = f"Research JSON: {research}\nInclude scope, constraints, acceptance_criteria. Keep under 120 lines."
        r = self.client.call("prompt_engineer", prompt, system)
        return r["text"]
