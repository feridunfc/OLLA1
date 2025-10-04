# -*- coding: utf-8 -*-
"""
Docker tabanlı güvenli sandbox.
Windows'ta Docker Desktop kuruluysa kullanılır. Aksi halde utils/sandbox.py içerisindeki
lokal fallback çalışır.
"""
import os, tempfile, textwrap
try:
    import docker
except Exception:
    docker = None

DEFAULT_IMAGE = "python:3.11-slim"

SECURE_OPTS = dict(
    network_mode="none",
    read_only=True,
    mem_limit="200m",
    cpu_quota=50000,
    security_opt=["no-new-privileges:true"],
    cap_drop=["ALL"],
)

class SecureDockerSandbox:
    def __init__(self, image: str = DEFAULT_IMAGE):
        self.image = image
        self.available = False
        if docker is None:
            return
        try:
            self.client = docker.from_env()
            # image pull etme sorumluluğunu kullanıcıya bırakalım (ilk çalıştırmada otomatik çekebilir)
            self.available = True
        except Exception:
            self.available = False

    def run_python(self, code: str, test_code: str = None, timeout: int = 30) -> tuple[bool,str]:
        if not self.available:
            return False, "Docker sandbox not available"

        with tempfile.TemporaryDirectory() as td:
            code_path = os.path.join(td, "code.py")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)

            test_path = None
            entry = f"python /mnt/code.py"
            if test_code:
                test_path = os.path.join(td, "tests.py")
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(test_code)
                entry = "python /mnt/tests.py"

            binds = {
                code_path: {"bind": "/mnt/code.py", "mode": "ro"}
            }
            if test_path:
                binds[test_path] = {"bind": "/mnt/tests.py", "mode": "ro"}

            try:
                out = self.client.containers.run(
                    self.image,
                    entry,
                    volumes=binds,
                    detach=False,
                    remove=True,
                    stdout=True,
                    stderr=True,
                    **SECURE_OPTS
                )
                return True, out.decode("utf-8", errors="ignore") if isinstance(out, (bytes,bytearray)) else str(out)
            except Exception as e:
                return False, str(e)
