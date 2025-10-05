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
