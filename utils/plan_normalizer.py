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
