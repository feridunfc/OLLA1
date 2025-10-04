# core/config.py
from __future__ import annotations
import os
from typing import List, Dict

# Ollama sunucusu (gerekirse değiştir)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# ---- Model Adayları (öncelik sırasına göre) ----
# config/models.py

## config/model_candidates.py

CANDIDATES = {
    "researcher": [
        "llama3.1:8b",
        "qwen2.5:7b-instruct",
        "llama3.2:3b-instruct",
        "qwen2.5:3b",
    ],
    "prompt_engineer": [
        "qwen2.5:7b-instruct",
        "qwen2.5:3b",
        "llama3.2:3b-instruct",
    ],
    "architect": [
        "qwen2.5:3b",              # hızlı ve JSON uyumu iyi
        "llama3.2:3b-instruct",
        "qwen2.5:7b-instruct",
        "llama3.1:8b",
    ],
    "coder": [
        "deepseek-coder:6.7b",
        "qwen2.5:7b-instruct",
        "qwen2.5:3b",
        "llama3.2:3b-instruct",
    ],
    "tester": [
        "qwen2.5:7b-instruct",
        "llama3.2:3b-instruct",
        "qwen2.5:3b",
    ],
    "debugger": [
        "deepseek-coder:6.7b",
        "qwen2.5:7b-instruct",
        "llama3.2:3b-instruct",
    ],
    "integrator": [
        "llama3.2:3b-instruct",
        "qwen2.5:3b",
        "qwen2.5:7b-instruct",
    ],
}

GLOBAL_FALLBACK = [
    "qwen2.5:3b",
    "llama3.2:3b-instruct",
    "llama3.1:8b",
]


# Son çare (makinende şu an yalnızca bu varsa buraya düşer)
LAST_RESORT = os.getenv("LAST_RESORT_MODEL", "llama3.2:1b")

# Varsayılan üretim ayarları
GENERATION_OPTS = {
    "temperature": float(os.getenv("GEN_TEMPERATURE", "0.3")),
    "top_p": float(os.getenv("GEN_TOP_P", "0.9")),
    "num_predict": int(os.getenv("GEN_NUM_PREDICT", "1024")),
}

def _installed_models() -> List[str]:
    """Ollama'da kurulu model adlarını döndürür (yoksa boş liste)."""
    try:
        import ollama
        data = ollama.list()
        return [m.get("model") or m.get("name") for m in data.get("models", [])]
    except Exception:
        return []

def choose_model(role: str) -> str:
    """
    Verilen rol için en uygun _kurulu_ modeli seç.
    1) CANDIDATES[role] içindeki ilk kurulu model
    2) GLOBAL_FALLBACK içindeki ilk kurulu model
    3) LAST_RESORT
    """
    installed = set(_installed_models())
    for m in CANDIDATES.get(role, []):
        if m in installed:
            return m
    for m in GLOBAL_FALLBACK:
        if m in installed:
            return m
    return LAST_RESORT
