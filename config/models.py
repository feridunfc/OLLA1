# -*- coding: utf-8 -*-
# Model adayları ve global fallback
CANDIDATES = {
    "researcher": ["llama3.1:8b","qwen2.5:7b-instruct","llama3.2:3b-instruct","qwen2.5:3b"],
    "prompt_engineer": ["qwen2.5:7b-instruct","qwen2.5:3b","llama3.2:3b-instruct"],
    "architect": ["qwen2.5:3b","llama3.2:3b-instruct","llama3.1:8b"],
    "coder": ["deepseek-coder:6.7b","qwen2.5:7b-instruct","qwen2.5:3b","llama3.2:3b-instruct"],
    "tester": ["qwen2.5:7b-instruct","llama3.2:3b-instruct","qwen2.5:3b"],
    "debugger": ["deepseek-coder:6.7b","qwen2.5:7b-instruct","llama3.2:3b-instruct"],
    "integrator": ["llama3.2:3b-instruct","qwen2.5:3b","qwen2.5:7b-instruct"],
}
GLOBAL_FALLBACK = ["llama3.2:3b-instruct","qwen2.5:3b","llama3.1:8b"]
