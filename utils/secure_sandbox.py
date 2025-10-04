from __future__ import annotations
import os, tempfile
from typing import Any, Dict, Optional
try:
    import docker  # type: ignore
except Exception:
    docker = None

DEFAULT_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")
DEFAULT_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "30"))
DEFAULT_MEM = os.getenv("SANDBOX_MEM", "512m")
DEFAULT_PIDS = int(os.getenv("SANDBOX_PIDS", "128"))
DEFAULT_TMPFS_SIZE = os.getenv("SANDBOX_TMPFS_SIZE", "100m")
DEFAULT_NO_NET = os.getenv("SANDBOX_NET_OFF", "1") == "1"
DEFAULT_READONLY = os.getenv("SANDBOX_READONLY", "1") == "1"

def _seccomp_opt() -> Optional[str]:
    custom = os.getenv("SANDBOX_SECCOMP_PATH")
    if custom and os.path.exists(custom):
        return f"seccomp={custom}"
    for c in ("/usr/share/docker/seccomp.json", "/etc/docker/seccomp.json"):
        if os.path.exists(c):
            return f"seccomp={c}"
    return None  # leave default

SECURITY_BASE = {
    "network_disabled": DEFAULT_NO_NET,
    "read_only": DEFAULT_READONLY,        # NOTE: docker SDK -> read_only (not read_only_rootfs)
    "cap_drop": ["ALL"],
    "mem_limit": DEFAULT_MEM,
    "pids_limit": DEFAULT_PIDS,
    "security_opt": ["no-new-privileges:true"],
    "tmpfs": {"/tmp": f"rw,noexec,nosuid,size={DEFAULT_TMPFS_SIZE}"},
}
_sec = _seccomp_opt()
if _sec:
    SECURITY_BASE["security_opt"] = SECURITY_BASE["security_opt"] + [_sec]  # type: ignore[index]

FORBIDDEN_SNIPPETS = ("import os","import sys","subprocess","__import__","eval(","exec(","open(")

class SecureSandboxRunner:
    """Run short Python snippets inside a hardened Docker container"""
    def __init__(self, image: str = DEFAULT_IMAGE, timeout: int = DEFAULT_TIMEOUT):
        if docker is None:
            raise RuntimeError("docker SDK not available. Install 'docker' and run Docker engine.")
        self.image = image
        self.timeout = timeout
        self.client = docker.from_env()  # type: ignore

    def run_code(self, code: str) -> Dict[str, Any]:
        low = code.lower()
        for frag in FORBIDDEN_SNIPPETS:
            if frag in low:
                return {"success": False, "status": 400, "logs": f"Forbidden pattern blocked: {frag}"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            host_path = f.name
        binds = {os.path.abspath(host_path): {"bind": "/app/main.py", "mode": "ro"}}
        try:
            container = self.client.containers.run(
                self.image, ["python", "/app/main.py"],
                detach=True, remove=True, volumes=binds, **SECURITY_BASE
            )
            result = container.wait(timeout=self.timeout)     # type: ignore[attr-defined]
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="ignore")  # type: ignore[attr-defined]
            code = result.get("StatusCode", 1)
            return {"success": code == 0, "status": code, "logs": logs}
        except Exception as e:
            return {"success": False, "status": 500, "logs": str(e)}
        finally:
            try: os.unlink(host_path)
            except Exception: pass
