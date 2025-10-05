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
