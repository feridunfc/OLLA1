
import os, time, httpx
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential
from config.models import CANDIDATES, GLOBAL_FALLBACK

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434")

class OllamaSmartClient:
    def __init__(self, timeout: float = 60.0):
        self.http = httpx.Client(base_url=OLLAMA_BASE, timeout=timeout)

    def _messages(self, system: str, prompt: str) -> List[Dict]:
        msgs = []
        if system:
            msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        return msgs

    def pick_model(self, role: str) -> str:
        prefer = CANDIDATES.get(role, [])
        for m in prefer:
            return m
        for m in GLOBAL_FALLBACK:
            return m
        return "llama3.2:3b-instruct"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=6))
    def call(self, role: str, prompt: str, system: str="", num_predict: int=600, temperature: float=0.2) -> Dict:
        model = self.pick_model(role)
        body = {"model": model, "prompt": (system + "\n\n" + prompt) if system else prompt, "stream": False, "options": {"num_predict": num_predict, "temperature": temperature, "top_p": 0.9}}
        t0 = time.time()
        r = self.http.post("/api/generate", json=body)
        r.raise_for_status()
        js = r.json()
        text = js.get("response") or js.get("content") or ""
        return {"ok": True, "text": text.strip(), "latency": time.time()-t0, "model": model}
