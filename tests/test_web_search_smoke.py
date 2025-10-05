import os
import pytest
from multi_ai.tools.web_search import WebSearchTool

@pytest.mark.asyncio
async def test_web_search_without_key():
    os.environ.pop("TAVILY_API_KEY", None)
    t = WebSearchTool()
    r = await t.arun("python")
    assert r.success is False and "missing" in (r.error or "").lower()
