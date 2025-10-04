
import json, streamlit as st
from pathlib import Path

st.set_page_config(page_title="OLLA1 Sprint Dashboard", layout="wide")
workdir = Path(st.sidebar.text_input("Workdir", value="./workdir"))

st.title("🧭 OLLA1 – Sprint Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Plan")
    plan_file = workdir / "plan.json"
    if plan_file.exists():
        st.json(json.loads(plan_file.read_text(encoding="utf-8")))
    else:
        st.info("Plan henüz bulunamadı.")

with col2:
    st.subheader("Results")
    res_file = workdir / "results.json"
    if res_file.exists():
        res = json.loads(res_file.read_text(encoding="utf-8"))
        st.json(res.get("integration"))
        st.divider()
        for tid, t in res.get("execution", {}).items():
            st.markdown(f"**{tid} — {t['title']}**  (ok={t['sandbox_ok']})")
            with st.expander("Sandbox output"):
                st.code(t.get("sandbox_output",""))
    else:
        st.info("Henüz sonuç yok.")

st.sidebar.subheader("Komut")
st.sidebar.code('python main.py "FastAPI\'ye JWT auth ekle" --auto', language="bash")
