# -*- coding: utf-8 -*-
"""
Güvenli çalıştırma katmanı:
1) Varsa Docker sandbox (secure_sandbox_docker) ile izole çalıştır
2) Yoksa lokal fallback (kısıtlı exec + AST denetimi + timeout)
"""
import ast, builtins, signal, sys, io, contextlib, time
from utils.secure_sandbox_docker import SecureDockerSandbox

FORBIDDEN_NAMES = {"__import__", "eval", "exec", "open", "compile", "input"}
FORBIDDEN_MODULES = {"os","sys","subprocess","shutil","socket","pathlib","requests","urllib","ctypes"}

class TimeoutError_(Exception): pass

class _Timeout:
    def __init__(self, seconds):
        self.seconds = seconds
    def __enter__(self):
        signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(self.seconds)
    def _handler(self, *_):
        raise TimeoutError_()
    def __exit__(self, exc_type, exc, tb):
        signal.alarm(0)

def _safe_ast_check(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        # import denetimi
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split('.')[0] in FORBIDDEN_MODULES:
                    raise ValueError(f"Forbidden import: {n.name}")
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_MODULES:
                raise ValueError(f"Forbidden import from: {node.module}")
        # isim denetimi
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"Forbidden name: {node.id}")

def _safe_exec(code: str, timeout: int = 10) -> tuple[bool,str]:
    _safe_ast_check(code)
    safe_builtins = {k: getattr(builtins,k) for k in ("abs","all","any","bool","dict","enumerate","float","int","len","list","max","min","print","range","str","sum","zip")}
    env = {"__builtins__": safe_builtins}
    buf = io.StringIO()
    try:
        with _Timeout(timeout), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(code, "<user>", "exec"), env, env)
        return True, buf.getvalue()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

class Sandbox:
    def __init__(self):
        self.docker = SecureDockerSandbox()

    def run(self, code: str, tests: str|None=None):
        # 1) Docker varsa
        if self.docker.available:
            ok, out = self.docker.run_python(code, tests)
            return ok, out

        # 2) Lokal fallback: kod + testleri ardışık çalıştır
        ok1, out1 = _safe_exec(code, timeout=10)
        if not ok1:
            return False, out1
        if tests:
            ok2, out2 = _safe_exec(tests, timeout=10)
            return ok2, (out1 + "\n" + out2 if ok2 else out2)
        return True, out1
