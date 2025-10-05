# scripts/apply_v41_integration.ps1
param(
  [string]$RepoRoot = ".",
  [switch]$Commit = $true
)

$ErrorActionPreference = "Stop"

function Ensure-Dir($p) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

# paths
$utils = Join-Path $RepoRoot "utils"
$orch  = Join-Path $RepoRoot "orchestrator"
$scriptsDir = Join-Path $RepoRoot "scripts"
$req = Join-Path $RepoRoot "requirements.txt"

Ensure-Dir $utils
Ensure-Dir $orch
Ensure-Dir $scriptsDir

# ---------- utils/secure_sandbox.py ----------
$secureSandbox = @'
from __future__ import annotations
import os, tempfile
from typing import Any, Dict, Optional
try:
    import docker  # type: ignore
except Exception:
    docker = None

DEFAULT_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")
DEFAULT_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "30"))
DEFAULT_MEM = os.getenv("SANDBOX_MEM", "512m")
DEFAULT_PIDS = int(os.getenv("SANDBOX_PIDS", "128"))
DEFAULT_TMPFS_SIZE = os.getenv("SANDBOX_TMPFS_SIZE", "100m")
DEFAULT_NO_NET = os.getenv("SANDBOX_NET_OFF", "1") == "1"
DEFAULT_READONLY = os.getenv("SANDBOX_READONLY", "1") == "1"

def _seccomp_opt() -> Optional[str]:
    custom = os.getenv("SANDBOX_SECCOMP_PATH")
    if custom and os.path.exists(custom):
        return f"seccomp={custom}"
    for c in ("/usr/share/docker/seccomp.json", "/etc/docker/seccomp.json"):
        if os.path.exists(c):
            return f"seccomp={c}"
    return None

SECURITY_BASE = {
    "network_disabled": DEFAULT_NO_NET,
    "read_only": DEFAULT_READONLY,
    "cap_drop": ["ALL"],
    "mem_limit": DEFAULT_MEM,
    "pids_limit": DEFAULT_PIDS,
    "security_opt": ["no-new-privileges:true"],
    "tmpfs": {"/tmp": f"rw,noexec,nosuid,size={DEFAULT_TMPFS_SIZE}"},
}
_sec = _seccomp_opt()
if _sec:
    SECURITY_BASE["security_opt"] = SECURITY_BASE["security_opt"] + [_sec]  # type: ignore[index]

FORBIDDEN_SNIPPETS = ("import os","import sys","subprocess","__import__","eval(","exec(","open(")

class SecureSandboxRunner:
    """Run short Python snippets inside a hardened Docker container."""
    def __init__(self, image: str = DEFAULT_IMAGE, timeout: int = DEFAULT_TIMEOUT):
        if docker is None:
            raise RuntimeError("docker SDK not available. Install 'docker' and run Docker engine.")
        self.image = image
        self.timeout = timeout
        self.client = docker.from_env()  # type: ignore

    def run_code(self, code: str) -> Dict[str, Any]:
        low = code.lower()
        for frag in FORBIDDEN_SNIPPETS:
            if frag in low:
                return {"success": False, "status": 400, "logs": f"Forbidden pattern blocked: {frag}"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            host_path = f.name
        binds = {os.path.abspath(host_path): {"bind": "/app/main.py", "mode": "ro"}}
        try:
            container = self.client.containers.run(
                self.image, ["python", "/app/main.py"],
                detach=True, remove=True, volumes=binds, **SECURITY_BASE
            )
            result = container.wait(timeout=self.timeout)     # type: ignore[attr-defined]
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="ignore")  # type: ignore[attr-defined]
            code = result.get("StatusCode", 1)
            return {"success": code == 0, "status": code, "logs": logs}
        except Exception as e:
            return {"success": False, "status": 500, "logs": str(e)}
        finally:
            try: os.unlink(host_path)
            except Exception: pass
'@

$secureSandboxPath = Join-Path $utils "secure_sandbox.py"
if (-not (Test-Path $secureSandboxPath)) { $secureSandbox | Set-Content -Encoding UTF8 $secureSandboxPath }

# ---------- utils/budget_guard.py ----------
$budgetGuard = @'
from __future__ import annotations
import os, sqlite3, threading
from dataclasses import dataclass
from datetime import datetime

DB_PATH = os.getenv("BUDGET_DB", "budget.db")
MONTHLY_LIMIT = float(os.getenv("MONTHLY_BUDGET", "100.0"))

@dataclass
class BudgetRecord:
    task_id: str
    usd: float
    status: str  # reserved | committed | released
    ts: str

class BudgetGuard:
    """Persistent budget guard using sqlite; reserve/commit/release."""
    def __init__(self, db_path: str = DB_PATH, monthly_limit: float = MONTHLY_LIMIT):
        self.db_path = db_path
        self.monthly_limit = monthly_limit
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS budget(
            task_id TEXT PRIMARY KEY, usd REAL, status TEXT, ts TEXT)""")
        self._conn.commit()

    def _used_this_month(self) -> float:
        cur = self._conn.execute(
          "SELECT COALESCE(SUM(usd),0) FROM budget WHERE status='committed' AND substr(ts,1,7)=?",
          (datetime.utcnow().strftime("%Y-%m"),)
        )
        val = cur.fetchone()[0]
        return float(val or 0.0)

    def reserve(self, task_id: str, est_usd: float) -> bool:
        with self._lock:
            if self._used_this_month() + est_usd > self.monthly_limit:
                return False
            self._conn.execute(
              "INSERT OR REPLACE INTO budget(task_id,usd,status,ts) VALUES(?,?, 'reserved', ?)",
              (task_id, float(est_usd), datetime.utcnow().isoformat())
            )
            self._conn.commit()
            return True

    def commit(self, task_id: str, actual_usd: float) -> None:
        with self._lock:
            self._conn.execute(
              "UPDATE budget SET status='committed', usd=?, ts=? WHERE task_id=?",
              (float(actual_usd), datetime.utcnow().isoformat(), task_id)
            )
            self._conn.commit()

    def release(self, task_id: str) -> None:
        with self._lock:
            self._conn.execute(
              "UPDATE budget SET status='released', ts=? WHERE task_id=?",
              (datetime.utcnow().isoformat(), task_id)
            )
            self._conn.commit()

    def usage_this_month(self) -> float:
        return self._used_this_month()
'@
$budgetGuardPath = Join-Path $utils "budget_guard.py"
if (-not (Test-Path $budgetGuardPath)) { $budgetGuard | Set-Content -Encoding UTF8 $budgetGuardPath }

# ---------- utils/observability.py ----------
$obs = @'
from __future__ import annotations
import os
from contextlib import contextmanager
from time import perf_counter
from prometheus_client import start_http_server, Counter, Histogram

PROM_PORT = int(os.getenv("PROMETHEUS_PORT", "8001"))
_PROM_STARTED = False

def ensure_prometheus_server() -> None:
    global _PROM_STARTED
    if not _PROM_STARTED:
        try:
            start_http_server(PROM_PORT)
            _PROM_STARTED = True
        except OSError:
            _PROM_STARTED = True  # already running

agent_calls  = Counter("agent_calls_total", "Total agent calls", ["agent","model","status"])
agent_latency = Histogram("agent_call_duration_seconds", "Agent call latency (s)", ["agent"])

@contextmanager
def measure_agent(agent: str, model: str):
    ensure_prometheus_server()
    t0 = perf_counter()
    try:
        yield
        dt = perf_counter() - t0
        agent_latency.labels(agent=agent).observe(dt)
        agent_calls.labels(agent=agent, model=model, status="success").inc()
    except Exception:
        dt = perf_counter() - t0
        agent_latency.labels(agent=agent).observe(dt)
        agent_calls.labels(agent=agent, model=model, status="error").inc()
        raise
'@
$obsPath = Join-Path $utils "observability.py"
if (-not (Test-Path $obsPath)) { $obs | Set-Content -Encoding UTF8 $obsPath }

# ---------- orchestrator/integrations_v41.py ----------
$orchHelper = @'
from __future__ import annotations
from typing import Any, Dict
from utils.budget_guard import BudgetGuard
from utils.observability import measure_agent

_bg = BudgetGuard()

async def guarded_agent_call(client: Any, role: str, model: str, prompt: str, run_id: str,
                             est_cost_usd: float = 0.02, stream: bool = False) -> Dict[str, Any]:
    """
    Tek noktadan güvenli çağrı:
      - Budget guard (reserve/commit/release)
      - Prometheus metrikleri (measure_agent)
      - İstenen client.call_role() çağrısı
    """
    task_id = f"agent:{role}:{run_id}"
    if not _bg.reserve(task_id, est_cost_usd):
        raise RuntimeError("Budget exceeded")

    with measure_agent(agent=role, model=model):
        try:
            # not: client.call_role rol->model eşleşmesini kendi içinde yapıyorsa 'model' paramını kullanmayabilir
            result = await client.call_role(role=role, prompt=prompt, stream=stream)
            # gerçek maliyet ölçümünüz varsa onu koyun; şimdilik est ile commit edelim
            _bg.commit(task_id, est_cost_usd)
            return result
        except Exception:
            _bg.release(task_id)
            raise
'@
$orchHelperPath = Join-Path $orch "integrations_v41.py"
if (-not (Test-Path $orchHelperPath)) { $orchHelper | Set-Content -Encoding UTF8 $orchHelperPath }

# ---------- requirements.txt (idempotent ekleme) ----------
if (-not (Test-Path $req)) {
  @"
docker
prometheus-client
"@ | Set-Content -Encoding UTF8 $req
} else {
  $txt = Get-Content $req -Raw
  if ($txt -notmatch "(?m)^\s*docker\s*$")            { Add-Content $req "`ndocker" }
  if ($txt -notmatch "(?m)^\s*prometheus-client\s*$") { Add-Content $req "`nprometheus-client" }
}

Write-Host "✅ Entegrasyon dosyaları hazırlandı." -ForegroundColor Green

if ($Commit) {
  git add utils orchestrator .\requirements.txt 2>$null
  git commit -m "feat: v4.1 integrations — BudgetGuard, Prometheus metrics, SecureSandbox + helper" 2>$null
  Write-Host "ℹ️ Commit atıldı. Push için: git push -u origin main" -ForegroundColor Yellow
}
