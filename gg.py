#!/usr/bin/env python3
# bootstrap_local_secure_upgrade.py
# OVERWRITE upgrade for MULTI_AI_Local_v4.2 -> security + stability + dashboard polish
import os, pathlib, textwrap, sys

ROOT = pathlib.Path(__file__).resolve().parent

FILES = {
    # ------------------------------ CONFIG ------------------------------
    "config/models.py": r'''
# -*- coding: utf-8 -*-
# Model adayları ve global fallback
CANDIDATES = {
    "researcher": ["llama3.1:8b","qwen2.5:7b-instruct","llama3.2:3b-instruct","qwen2.5:3b"],
    "prompt_engineer": ["qwen2.5:7b-instruct","qwen2.5:3b","llama3.2:3b-instruct"],
    "architect": ["qwen2.5:3b","llama3.2:3b-instruct","llama3.1:8b"],
    "coder": ["deepseek-coder:6.7b","qwen2.5:7b-instruct","qwen2.5:3b","llama3.2:3b-instruct"],
    "tester": ["qwen2.5:7b-instruct","llama3.2:3b-instruct","qwen2.5:3b"],
    "debugger": ["deepseek-coder:6.7b","qwen2.5:7b-instruct","llama3.2:3b-instruct"],
    "integrator": ["llama3.2:3b-instruct","qwen2.5:3b","qwen2.5:7b-instruct"],
}
GLOBAL_FALLBACK = ["llama3.2:3b-instruct","qwen2.5:3b","llama3.1:8b"]
''',

    # ------------------------------ CORE -------------------------------
    "core/ollama_smart_client.py": r'''
# -*- coding: utf-8 -*-
import time, re
from tenacity import retry, stop_after_attempt, wait_exponential
import ollama
from config.models import CANDIDATES, GLOBAL_FALLBACK

ARCHITECT_OPTIONS = {"temperature": 0.2, "top_p": 0.9, "num_predict": 1024}
DEFAULT_OPTIONS   = {"temperature": 0.2, "top_p": 0.9, "num_predict": 768}

def _strip_code_fences(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    # ```lang ... ``` veya ``` ... ``` aralıklarını temizle
    s = re.sub(r"^```[\w-]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

class OllamaSmartClient:
    def __init__(self):
        try:
            lst = ollama.list().get("models", [])
            self.available = {m["name"] for m in lst}
        except Exception:
            self.available = set()

    def pick_model(self, role: str) -> str:
        prefer = CANDIDATES.get(role, [])
        for m in prefer:
            if (self.available and m in self.available) or (not self.available):
                return m
        for m in GLOBAL_FALLBACK:
            if (self.available and m in self.available) or (not self.available):
                return m
        return GLOBAL_FALLBACK[-1]

    def _msgs(self, system: str, prompt: str):
        msgs=[]
        if system: msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        return msgs

    def _role_opts(self, role: str):
        if role == "architect":
            return {**DEFAULT_OPTIONS, **ARCHITECT_OPTIONS}
        return DEFAULT_OPTIONS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
    def call(self, role: str, prompt: str, system: str="", options: dict=None):
        model = self.pick_model(role)
        opts = {**self._role_opts(role), **(options or {})}
        t0 = time.time()
        res = ollama.chat(model=model, messages=self._msgs(system,prompt), options=opts)
        text = _strip_code_fences((res.get("message",{}) or {}).get("content","").strip())
        return {"ok": True, "text": text, "latency": time.time()-t0, "model": model, "options": opts}
''',

    # ------------------------------ UTILS ------------------------------
    "utils/secure_sandbox_docker.py": r'''
# -*- coding: utf-8 -*-
"""
Docker tabanlı güvenli sandbox.
Windows'ta Docker Desktop kuruluysa kullanılır. Aksi halde utils/sandbox.py içerisindeki
lokal fallback çalışır.
"""
import os, tempfile, textwrap
try:
    import docker
except Exception:
    docker = None

DEFAULT_IMAGE = "python:3.11-slim"

SECURE_OPTS = dict(
    network_mode="none",
    read_only=True,
    mem_limit="200m",
    cpu_quota=50000,
    security_opt=["no-new-privileges:true"],
    cap_drop=["ALL"],
)

class SecureDockerSandbox:
    def __init__(self, image: str = DEFAULT_IMAGE):
        self.image = image
        self.available = False
        if docker is None:
            return
        try:
            self.client = docker.from_env()
            # image pull etme sorumluluğunu kullanıcıya bırakalım (ilk çalıştırmada otomatik çekebilir)
            self.available = True
        except Exception:
            self.available = False

    def run_python(self, code: str, test_code: str = None, timeout: int = 30) -> tuple[bool,str]:
        if not self.available:
            return False, "Docker sandbox not available"

        with tempfile.TemporaryDirectory() as td:
            code_path = os.path.join(td, "code.py")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)

            test_path = None
            entry = f"python /mnt/code.py"
            if test_code:
                test_path = os.path.join(td, "tests.py")
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(test_code)
                entry = "python /mnt/tests.py"

            binds = {
                code_path: {"bind": "/mnt/code.py", "mode": "ro"}
            }
            if test_path:
                binds[test_path] = {"bind": "/mnt/tests.py", "mode": "ro"}

            try:
                out = self.client.containers.run(
                    self.image,
                    entry,
                    volumes=binds,
                    detach=False,
                    remove=True,
                    stdout=True,
                    stderr=True,
                    **SECURE_OPTS
                )
                return True, out.decode("utf-8", errors="ignore") if isinstance(out, (bytes,bytearray)) else str(out)
            except Exception as e:
                return False, str(e)
''',

    "utils/sandbox.py": r'''
# -*- coding: utf-8 -*-
"""
Güvenli çalıştırma katmanı:
1) Varsa Docker sandbox (secure_sandbox_docker) ile izole çalıştır
2) Yoksa lokal fallback (kısıtlı exec + AST denetimi + timeout)
"""
import ast, builtins, signal, sys, io, contextlib, time
from utils.secure_sandbox_docker import SecureDockerSandbox

FORBIDDEN_NAMES = {"__import__", "eval", "exec", "open", "compile", "input"}
FORBIDDEN_MODULES = {"os","sys","subprocess","shutil","socket","pathlib","requests","urllib","ctypes"}

class TimeoutError_(Exception): pass

class _Timeout:
    def __init__(self, seconds):
        self.seconds = seconds
    def __enter__(self):
        signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(self.seconds)
    def _handler(self, *_):
        raise TimeoutError_()
    def __exit__(self, exc_type, exc, tb):
        signal.alarm(0)

def _safe_ast_check(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        # import denetimi
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split('.')[0] in FORBIDDEN_MODULES:
                    raise ValueError(f"Forbidden import: {n.name}")
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_MODULES:
                raise ValueError(f"Forbidden import from: {node.module}")
        # isim denetimi
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"Forbidden name: {node.id}")

def _safe_exec(code: str, timeout: int = 10) -> tuple[bool,str]:
    _safe_ast_check(code)
    safe_builtins = {k: getattr(builtins,k) for k in ("abs","all","any","bool","dict","enumerate","float","int","len","list","max","min","print","range","str","sum","zip")}
    env = {"__builtins__": safe_builtins}
    buf = io.StringIO()
    try:
        with _Timeout(timeout), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(code, "<user>", "exec"), env, env)
        return True, buf.getvalue()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

class Sandbox:
    def __init__(self):
        self.docker = SecureDockerSandbox()

    def run(self, code: str, tests: str|None=None):
        # 1) Docker varsa
        if self.docker.available:
            ok, out = self.docker.run_python(code, tests)
            return ok, out

        # 2) Lokal fallback: kod + testleri ardışık çalıştır
        ok1, out1 = _safe_exec(code, timeout=10)
        if not ok1:
            return False, out1
        if tests:
            ok2, out2 = _safe_exec(tests, timeout=10)
            return ok2, (out1 + "\n" + out2 if ok2 else out2)
        return True, out1
''',

    "utils/plan_normalizer.py": r'''
# -*- coding: utf-8 -*-
"""
LLM'den gelen planı normalize eder.
Beklenen şema:
{
  "sprint_title": str,
  "sprint_goal": str,
  "weeks": [
    {"week_number": int, "tasks":[
        {"task_id": str, "title": str, "description": str,
         "agent_type": "coder"|"tester"|"integrator",
         "dependencies": list[str], "estimated_hours": int}
    ]}
  ]
}
Türkçe alan adlarını da dönüştürür.
"""
ROLE_MAP = {
    "yazılımcı": "coder", "coder": "coder", "developer":"coder",
    "testçi": "tester", "tester": "tester",
    "entegrator":"integrator", "integrator":"integrator"
}

def _coerce_int(v, d=1):
    try: return int(v)
    except: return d

def _coerce_role(v, d="coder"):
    v = (v or "").strip().lower()
    return ROLE_MAP.get(v, "coder") if v else d

def normalize_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        return _fallback()
    # alan isim varyasyonları
    title = plan.get("sprint_title") or plan.get("sprint_baslik") or plan.get("title") or "Sprint"
    goal  = plan.get("sprint_goal") or plan.get("sprint_hedef") or plan.get("goal") or ""
    weeks = plan.get("weeks") or plan.get("haftalar") or []

    norm_weeks=[]
    for i, w in enumerate(weeks, start=1):
        wnum = w.get("week_number") or w.get("hafta_no") or i
        raw_tasks = w.get("tasks") or w.get("gorevler") or []
        nt=[]
        for t in raw_tasks:
            nt.append({
                "task_id": str(t.get("task_id") or t.get("gorev_id") or f"T{i}{len(nt)+1}"),
                "title": t.get("title") or t.get("baslik") or "Task",
                "description": t.get("description") or t.get("aciklama") or "",
                "agent_type": _coerce_role(t.get("agent_type") or t.get("ajan_tipi")),
                "dependencies": t.get("dependencies") or t.get("bagimliliklar") or [],
                "estimated_hours": _coerce_int(t.get("estimated_hours") or t.get("tahmini_saat") or 2),
            })
        norm_weeks.append({"week_number": _coerce_int(wnum, i), "tasks": nt})

    out = {"sprint_title": title, "sprint_goal": goal, "weeks": norm_weeks}
    if not out["weeks"]:
        out = _fallback()
    return out

def _fallback():
    return {
        "sprint_title":"Fallback Sprint",
        "sprint_goal":"Baseline",
        "weeks":[{"week_number":1,"tasks":[{
            "task_id":"T-1","title":"Scaffold","description":"Create minimal structure",
            "agent_type":"coder","dependencies":[],"estimated_hours":2
        }]}]
    }
''',

    # --------------------------- ORCHESTRATOR --------------------------
    "orchestrator/human_loop_orchestrator.py": r'''
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
''',

    # ----------------------------- DASHBOARD ---------------------------
    "dashboard/app.py": r'''
# -*- coding: utf-8 -*-
import streamlit as st, os, json, glob

st.set_page_config(page_title="MULTI_AI Local v4.2", page_icon="🤖", layout="wide")
st.title("🤖 MULTI_AI Local v4.2 — Dashboard")
st.caption("Yerel Ollama + Güvenli Sandbox + HITL")

workdir = "./workdir"
os.makedirs(workdir, exist_ok=True)

with st.sidebar:
    st.header("🎛️ Kontrol")
    goal = st.text_area("Sprint hedefi", "FastAPI'ye JWT auth ekle")
    st.write("CLI'da `python main.py \"<hedef>\"` komutu ile çalıştırın.")
    st.divider()
    st.subheader("📦 Çıktı dosyaları")
    st.code("workdir/plan.json\nworkdir/results.json")
    st.divider()
    try:
        import ollama
        models = ollama.list().get("models",[])
        st.success(f"Ollama modelleri: {len(models)}")
    except:
        st.warning("Ollama erişilemedi (ollama serve?)")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📋 Planlar")
    plan_path = os.path.join(workdir,"plan.json")
    if os.path.exists(plan_path):
        st.json(json.load(open(plan_path,"r",encoding="utf-8")))
    else:
        st.info("Henüz plan yok.")

with col2:
    st.subheader("📦 Sonuçlar")
    res_path = os.path.join(workdir,"results.json")
    if os.path.exists(res_path):
        data = json.load(open(res_path,"r",encoding="utf-8"))
        st.metric("Görev sayısı", sum(len(w['tasks']) for w in data.get("plan",{}).get("weeks",[])))
        pass_cnt = sum(1 for k,v in data.get("execution",{}).items() if v.get("sandbox_ok"))
        st.metric("Sandbox PASS", pass_cnt)
        with st.expander("Tüm sonuç JSON"):
            st.json(data)
    else:
        st.info("Henüz sonuç yok.")
''',

    # ----------------------------- SCRIPTS -----------------------------
    "scripts/github_init.ps1": r'''
param(
  [string]$RepoName = "multi-ai-local-v42",
  [string]$Remote = "origin",
  [string]$GitHubUrl = ""
)
if (-not (Test-Path .git)) { git init }
git add .
git commit -m "chore: bootstrap v4.2 local secure upgrade"
if ($GitHubUrl -ne "") {
  git remote remove $Remote 2>$null
  git remote add $Remote $GitHubUrl
  git branch -M main
  git push -u $Remote main
  Write-Host "✅ pushed to $GitHubUrl"
} else {
  Write-Host "ℹ️  Remote URL verilmedi. 'scripts/github_init.ps1 -GitHubUrl https://github.com/<user>/<repo>.git'"
}
''',

    # --------------------------- REQUIREMENTS --------------------------
    "requirements.txt": r'''
ollama>=0.1.7
streamlit>=1.28.0
docker>=6.0.0
pydantic>=2.0.0
tenacity>=8.2.0
httpx>=0.25.0
python-dotenv>=1.0.0
prometheus_client>=0.20.0
''',
}

def write_file(path: pathlib.Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

def main():
    created = []
    for rel, content in FILES.items():
        p = ROOT / rel
        write_file(p, content)
        created.append(str(p.relative_to(ROOT)))
    print("✅ Overwrite tamam. Güncellenen dosyalar:")
    for c in created:
        print("  -", c)
    print("\n➕ Sonraki adımlar:")
    print("1) pip install -r requirements.txt")
    print("2) (Windows) Docker Desktop açıksa sandbox otomatik Docker ile güvenli çalışır.")
    print("3) main.py ile normal akışı çalıştırın; dashboard için:")
    print("   streamlit run dashboard/app.py")
    print("\nGitHub push (opsiyonel):")
    print("   pwsh scripts/github_init.ps1 -GitHubUrl https://github.com/<user>/<repo>.git")

if __name__ == "__main__":
    main()
