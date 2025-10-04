# tools/materialize_results.py
import json, os, sys, textwrap

WORKDIR = sys.argv[1] if len(sys.argv) > 1 else "./workdir"
OUTDIR  = sys.argv[2] if len(sys.argv) > 2 else "./materialized"

os.makedirs(OUTDIR, exist_ok=True)
with open(os.path.join(WORKDIR,"results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

execu = data.get("execution", {})
for tid, payload in execu.items():
    code  = payload.get("code") or ""
    tests = payload.get("tests") or ""
    if code.strip():
        with open(os.path.join(OUTDIR, f"{tid.lower()}_code.py"), "w", encoding="utf-8") as f:
            f.write(code if code.endswith("\n") else code + "\n")
    if tests.strip():
        with open(os.path.join(OUTDIR, f"{tid.lower()}_tests.py"), "w", encoding="utf-8") as f:
            f.write(tests if tests.endswith("\n") else tests + "\n")

print(f"✅ Yazıldı -> {OUTDIR} (kod ve test dosyaları)")
