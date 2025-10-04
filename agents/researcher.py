
class ResearcherAgent:
    def __init__(self, client): self.client = client
    def run(self, goal: str) -> dict:
        return {"goals":[goal],"assumptions":[],"risks":[],"open_questions":[],"tech_stack":[],"complexity":"medium"}
