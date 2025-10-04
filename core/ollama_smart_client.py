# -*- coding: utf-8 -*-
import time, re
from tenacity import retry, stop_after_attempt, wait_exponential
import ollama
from config.models import CANDIDATES, GLOBAL_FALLBACK

ARCHITECT_OPTIONS = {"temperature": 0.2, "top_p": 0.9, "num_predict": 1024}
DEFAULT_OPTIONS   = {"temperature": 0.2, "top_p": 0.9, "num_predict": 768}

def _strip_code_fences(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    # ```lang ... ``` veya ``` ... ``` aralıklarını temizle
    s = re.sub(r"^```[\w-]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

class OllamaSmartClient:
    def __init__(self):
        try:
            lst = ollama.list().get("models", [])
            self.available = {m["name"] for m in lst}
        except Exception:
            self.available = set()

    def pick_model(self, role: str) -> str:
        prefer = CANDIDATES.get(role, [])
        for m in prefer:
            if (self.available and m in self.available) or (not self.available):
                return m
        for m in GLOBAL_FALLBACK:
            if (self.available and m in self.available) or (not self.available):
                return m
        return GLOBAL_FALLBACK[-1]

    def _msgs(self, system: str, prompt: str):
        msgs=[]
        if system: msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        return msgs

    def _role_opts(self, role: str):
        if role == "architect":
            return {**DEFAULT_OPTIONS, **ARCHITECT_OPTIONS}
        return DEFAULT_OPTIONS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
    def call(self, role: str, prompt: str, system: str="", options: dict=None):
        model = self.pick_model(role)
        opts = {**self._role_opts(role), **(options or {})}
        t0 = time.time()
        res = ollama.chat(model=model, messages=self._msgs(system,prompt), options=opts)
        text = _strip_code_fences((res.get("message",{}) or {}).get("content","").strip())
        return {"ok": True, "text": text, "latency": time.time()-t0, "model": model, "options": opts}
