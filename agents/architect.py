
class ArchitectAgent:
    def __init__(self, client): self.client = client
    def run(self, directive: str) -> dict:
        return {
            "sprint_title":"JWT Auth Sprint",
            "sprint_goal":"Add JWT authentication to FastAPI with in-memory users and tests.",
            "weeks":[{"week_number":1,"tasks":[
                {"task_id":"T1","title":"Proje iskeleti & settings","description":"Setup FastAPI app & settings","agent_type":"coder","dependencies":[],"estimated_hours":2},
                {"task_id":"T2","title":"/register (hash, doğrulama)","description":"Implement registration with passlib[bcrypt]","agent_type":"coder","dependencies":["T1"],"estimated_hours":2},
                {"task_id":"T3","title":"JWT helper (create/verify)","description":"pyjwt HS256 dev-secret exp=30m","agent_type":"coder","dependencies":["T1"],"estimated_hours":2},
                {"task_id":"T4","title":"/login (token döndür)","description":"Generate JWT","agent_type":"coder","dependencies":["T2","T3"],"estimated_hours":2},
                {"task_id":"T5","title":"get_current_user dependency","description":"Decode JWT and fetch user","agent_type":"coder","dependencies":["T3"],"estimated_hours":2},
                {"task_id":"T6","title":"/me korumalı endpoint","description":"Bearer required","agent_type":"coder","dependencies":["T5"],"estimated_hours":1},
                {"task_id":"T7","title":"login & me testleri","description":"pytest + httpx AsyncClient","agent_type":"tester","dependencies":["T4","T6"],"estimated_hours":2},
                {"task_id":"T8","title":"küçük düzeltmeler","description":"Final polish","agent_type":"coder","dependencies":["T7"],"estimated_hours":1},
            ]}]
        }
