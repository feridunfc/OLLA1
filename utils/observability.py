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
            _PROM_STARTED = True  # already in use

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
