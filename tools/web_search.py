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
