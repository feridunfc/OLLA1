
import traceback, io, contextlib, ast

FORBIDDEN = {"__import__", "eval(", "exec(", "open(", "subprocess", "os.", "sys."}

def safe_exec(code: str):
    for bad in FORBIDDEN:
        if bad in code:
            return False, f"Forbidden pattern detected: {bad}"
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    env = {"__builtins__": {"print": print, "range": range, "len": len}}
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, env, env)
        return True, stdout.getvalue()
    except Exception:
        return False, traceback.format_exc()

class Sandbox:
    def run(self, code: str, tests: str = ""):
        ok, out = safe_exec(code)
        if not ok:
            return False, out
        if tests:
            tok, tout = safe_exec(tests)
            return tok, tout
        return ok, out
