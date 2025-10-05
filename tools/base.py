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
