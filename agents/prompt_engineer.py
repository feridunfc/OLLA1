
class PromptEngineerAgent:
    def __init__(self, client): self.client = client
    def craft_for_architect(self, research: dict) -> str:
        return ("Architect, output strict JSON: {sprint_title, sprint_goal, weeks:[{week_number, tasks:[{task_id,title,description,agent_type,dependencies,estimated_hours}]}]} "
                "agent_type in {coder,tester,integrator}.")
