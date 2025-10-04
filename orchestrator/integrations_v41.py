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
