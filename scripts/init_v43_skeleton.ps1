param(
  [string]$RepoRoot = ".",
  [switch]$Commit
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

# Klasörler
$dirs = @("tools","orchestrator","auditor","supervisor","config",".github/workflows","prompts","utils","scripts")
$dirs | ForEach-Object { if (!(Test-Path $_)) { New-Item -ItemType Directory -Path $_ | Out-Null } }

# Policy dosyası (örnek)
@"
roles:
  researcher: [web_search]
  prompt_engineer: [web_search]
  coder: [file_patch, linter]
  tester: [linter, db_query]
  integrator: [file_patch, db_query]
approvals:
  file_patch.delete:
    require_human: true
limits:
  web_search:
    per_task_max_calls: 5
    per_call_timeout_sec: 15
"@ | Set-Content -Encoding UTF8 .\config\tools_policy.yaml

# BaseTool iskeleti
@"
from typing import TypedDict, Optional, Literal
from abc import ABC, abstractmethod

class ToolContext(TypedDict, total=False):
    task_id: str
    role: str
    cwd: str
    env: dict
    timeout_sec: int
    budget_guard: object
    rate_bucket: object
    sandbox: object
    approvals: object

class ToolResult(TypedDict):
    ok: bool
    output: str
    artifacts: list[str]
    cost: float
    telemetry: dict

class BaseTool(ABC):
    name: str = "base"
    description: str = "abstract tool"
    @abstractmethod
    def run(self, params: dict, ctx: ToolContext) -> ToolResult:
        raise NotImplementedError
"@ | Set-Content -Encoding UTF8 .\tools\base.py

# WebSearchTool iskeleti (SerpAPI/Tavily anahtarını ENV'den okur)
@"
import os, json, time
from .base import BaseTool, ToolContext, ToolResult

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "web search via SerpAPI/Tavily"

    def __init__(self):
        self.provider = os.getenv("WEB_SEARCH_PROVIDER","serpapi")
        self.key = os.getenv("WEB_SEARCH_KEY")

    def run(self, params: dict, ctx: ToolContext) -> ToolResult:
        q = params.get("query","").strip()
        if not q:
            return {"ok": False, "output": "empty query", "artifacts": [], "cost": 0.0, "telemetry": {}}

        # rate & budget checks (caller tarafında yapılmış varsay)
        # demo: gerçek HTTP çağrısı yok; stub cevap
        result = {"query": q, "items": [{"title":"stub","url":"https://example.com","snippet":"..."}]}
        return {"ok": True, "output": json.dumps(result, ensure_ascii=False), "artifacts": [], "cost": 0.001, "telemetry": {"provider": self.provider}}
"@ | Set-Content -Encoding UTF8 .\tools\web_search.py

# FilePatcherTool iskeleti
@"
import difflib, pathlib, io
from .base import BaseTool, ToolContext, ToolResult

class FilePatcherTool(BaseTool):
    name = "file_patch"
    description = "apply unified diff to files (non-destructive)"

    def run(self, params: dict, ctx: ToolContext) -> ToolResult:
        diff_text = params.get("diff","")
        if not diff_text:
            return {"ok": False, "output": "missing diff", "artifacts": [], "cost": 0.0, "telemetry": {}}
        # TODO: gerçek patch uygulama (sadece ekleme/değişiklik; delete -> approval)
        return {"ok": True, "output": "patch applied (stub)", "artifacts": [], "cost": 0.0, "telemetry": {}}
"@ | Set-Content -Encoding UTF8 .\tools\file_patcher.py

# DB Query Tool iskeleti
@"
from .base import BaseTool, ToolContext, ToolResult

class DatabaseQueryTool(BaseTool):
    name = "db_query"
    description = "safe read-only SQL (SELECT/*)"

    def run(self, params: dict, ctx: ToolContext) -> ToolResult:
        sql = params.get("sql","").strip().lower()
        if not sql.startswith("select") and not sql.startswith("pragma") and not sql.startswith("show"):
            return {"ok": False, "output": "write statements are not allowed", "artifacts": [], "cost": 0.0, "telemetry": {}}
        # TODO: gerçek bağlantı ve sorgu; şu an stub
        return {"ok": True, "output": "[]", "artifacts": [], "cost": 0.0, "telemetry": {}}
"@ | Set-Content -Encoding UTF8 .\tools\db_query.py

# ReAct yürütücü iskeleti
@"
from dataclasses import dataclass
from typing import Literal, List, Dict, Any

@dataclass
class ExecutionStep:
    kind: Literal['llm','tool']
    name: str
    params: Dict[str, Any]
    requires_approval: bool = False
    stop_condition: str | None = None

async def run_task(steps: List[ExecutionStep], ctx) -> Dict:
    # TODO: Think -> Act -> Observe döngüsü; metrics & budget guard çağrıları
    return {'ok': True, 'steps': len(steps)}
"@ | Set-Content -Encoding UTF8 .\orchestrator\react_executor.py

# Auditor export şablonları
@"
### HARİCİ KOD DENETİMİ TALEBİ ###

**Projenin Amacı:**
{sprint_goal}

**Mimari Plan:**
{architecture_plan}

**Üretilen Kod Dosyaları:**
{files_section}

Lütfen şu kriterlere göre değerlendir:
- Kod Kalitesi (okunabilirlik, modülerlik)
- Güvenlik (authz, SQLi, XSS)
- Performans
- En İyi Pratikler
- En kritik 3 iyileştirme önerisi
"@ | Set-Content -Encoding UTF8 .\prompts\audit_prompt_template.txt

# CI (minimum)
@"
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt || true
      - run: pip install pytest pip-audit bandit cyclonedx-bom || true
      - run: pytest -q || true
      - run: pip-audit --fail-on high || true
      - run: bandit -r . || true
      - run: cyclonedx-bom -o bom.xml || true
      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: bom.xml
"@ | Set-Content -Encoding UTF8 .\.github\workflows\ci.yml

if ($Commit) {
  git add .
  git commit -m "feat(v4.3): tools layer, policy, react executor stubs, CI base"
}
Write-Host "✅ v4.3 skeleton written."
