# -*- coding: utf-8 -*-
import os, json
from datetime import datetime
from core.ollama_smart_client import OllamaSmartClient
from utils.sandbox import Sandbox
from utils.plan_normalizer import normalize_plan

# Ajanlar (mevcut ajans modüllerini kullanıyoruz)
from agents.researcher import ResearcherAgent
from agents.prompt_engineer import PromptEngineerAgent
from agents.architect import ArchitectAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.debugger import DebuggerAgent
from agents.integrator import IntegratorAgent

class HumanLoopOrchestrator:
    def __init__(self, workdir: str="./workdir"):
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.client = OllamaSmartClient()
        self.sandbox = Sandbox()

    def _approve(self, title: str, payload) -> bool:
        print(f"\n{title}\n")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return input("Onaylıyor musunuz? [y/N] ").strip().lower()=="y"

    def _save_json(self, name: str, obj: dict):
        with open(os.path.join(self.workdir,name),"w",encoding="utf-8") as f:
            json.dump(obj,f,indent=2,ensure_ascii=False)

    async def run_sprint(self, goal: str):
        print(f"🎯 Sprint: {goal}")
        print("🧠 Mode: FULL-LOCAL (Ollama)")

        # PHASE 1 — Discovery
        print("\n🔍 PHASE 1 — Discovery")
        research = await ResearcherAgent(self.client).run(goal)
        if not self._approve("Discovery", research): return

        # PHASE 2 — Planning
        print("\n📋 PHASE 2 — Planning")
        directive = await PromptEngineerAgent(self.client).craft_for_architect(research)
        raw_plan = await ArchitectAgent(self.client).run(directive)
        plan = normalize_plan(raw_plan)
        if not self._approve("Plan", plan): return
        self._save_json("plan.json", plan)

        # PHASE 3 — Execution
        print("\n⚡ PHASE 3 — Execution")
        results = {}
        for wk in plan.get("weeks", []):
            for task in wk.get("tasks", []):
                tid = task["task_id"]; role = task.get("agent_type", "coder")
                title = task["title"]
                print(f"\n🛠️  Task: [{tid}] {title}  ({role})")

                if role == "coder":
                    code = await CoderAgent(self.client).run(task["description"])
                    tests = await TesterAgent(self.client).run(code)
                    ok, out = self.sandbox.run(code, tests)
                    if not ok:
                        print("   🔧 Debugging...")
                        fixed = await DebuggerAgent(self.client).run(code, out)
                        ok2, out2 = self.sandbox.run(fixed, tests)
                        code, out, ok = (fixed, out2, ok2)
                    results[tid] = {"title":title,"role":role,"code":code,"tests":tests,"sandbox_ok":ok,"sandbox_output":out[:2000],"sandbox_error":""}
                elif role == "tester":
                    # bağımsız tester görevi kod context'i yoksa geç
                    results[tid] = {"title":title,"role":role,"note":"Standalone tester task skipped (no target code id specified)."}
                else:
                    results[tid] = {"title":title,"role":role,"note":"No-op"}

        # PHASE 4 — Integration
        print("\n🔄 PHASE 4 — Integration")
        integ = await IntegratorAgent(self.client).run(results)
        if not self._approve("Integration", integ): return

        final = {
            "goal": goal, "research": research, "plan": plan,
            "execution": results, "integration": integ,
            "ts": datetime.now().isoformat()
        }
        self._save_json("results.json", final)
        print("✅ Sprint tamamlandı.")
