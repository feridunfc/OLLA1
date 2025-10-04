
import os, json
from datetime import datetime
from core.ollama_smart_client import OllamaSmartClient
from agents.researcher import ResearcherAgent
from agents.prompt_engineer import PromptEngineerAgent
from agents.architect import ArchitectAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.debugger import DebuggerAgent
from agents.integrator import IntegratorAgent
from utils.sandbox import Sandbox
from utils.metrics import Metrics
from utils.logger import Logger
from utils.plan_normalizer import normalize_plan

class HumanLoopOrchestrator:
    def __init__(self, workdir: str="./workdir", auto: bool=False):
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.client = OllamaSmartClient()
        self.sandbox = Sandbox()
        self.metrics = Metrics(os.path.join(workdir,"metrics.jsonl"))
        self.logger = Logger(os.path.join(workdir,"run.log"))
        self.auto = auto
    def _approve(self, title: str, payload) -> bool:
        print(f"\n{title}\n" + json.dumps(payload, indent=2, ensure_ascii=False))
        self.logger.write_block(title, payload)
        if self.auto: return True
        return input("Onaylıyor musunuz? [y/N] ").strip().lower()=="y"
    def _save_json(self, name: str, obj: dict):
        with open(os.path.join(self.workdir,name),"w",encoding="utf-8") as f:
            json.dump(obj,f,indent=2,ensure_ascii=False)
    def run_sprint(self, goal: str):
        print(f"🎯 Sprint: {goal}")
        print("🧠 Mode: FULL-LOCAL (Ollama)")
        print("\n🔍 PHASE 1 — Discovery")
        research = ResearcherAgent(self.client).run(goal)
        if not self._approve("Discovery", research): return
        print("\n📋 PHASE 2 — Planning")
        directive = PromptEngineerAgent(self.client).craft_for_architect(research)
        plan = ArchitectAgent(self.client).run(directive)
        plan = normalize_plan(plan)
        if not self._approve("Plan", plan): return
        self._save_json("plan.json", plan)
        print("\n⚡ PHASE 3 — Execution")
        results = {}
        for wk in plan.get("weeks", []):
            for task in wk.get("tasks", []):
                role = task.get("agent_type")
                title = task.get("title")
                print(f"\n🛠️  Task: [{task['task_id']}] {title}  ({role})")
                if role != "coder": continue
                code = CoderAgent(self.client).run(task["description"])
                tests = TesterAgent(self.client).run(code)
                ok, out = self.sandbox.run(code, tests)
                if not ok:
                    fixed = DebuggerAgent(self.client).run(code, out)
                    ok2, out2 = self.sandbox.run(fixed, tests)
                    code, out, ok = (fixed, out2, ok2)
                results[task["task_id"]] = {"title":title,"role":role,"code":code,"tests":tests,"sandbox_ok":ok,"sandbox_output":out[:2000]}
                self.metrics.write({"task_id":task["task_id"] ,"ok":ok})
        print("\n🔄 PHASE 4 — Integration")
        integ = IntegratorAgent(self.client).run(results)
        if not self._approve("Integration", integ): return
        final = {"goal":goal,"research":research,"plan":plan,"execution":results,"integration":integ,"ts":datetime.now().isoformat()}
        self._save_json("results.json", final)
        print("✅ Sprint tamamlandı.")
