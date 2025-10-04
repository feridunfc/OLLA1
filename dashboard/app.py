# -*- coding: utf-8 -*-
import streamlit as st, os, json, glob

st.set_page_config(page_title="MULTI_AI Local v4.2", page_icon="🤖", layout="wide")
st.title("🤖 MULTI_AI Local v4.2 — Dashboard")
st.caption("Yerel Ollama + Güvenli Sandbox + HITL")

workdir = "./workdir"
os.makedirs(workdir, exist_ok=True)

with st.sidebar:
    st.header("🎛️ Kontrol")
    goal = st.text_area("Sprint hedefi", "FastAPI'ye JWT auth ekle")
    st.write("CLI'da `python main.py \"<hedef>\"` komutu ile çalıştırın.")
    st.divider()
    st.subheader("📦 Çıktı dosyaları")
    st.code("workdir/plan.json\nworkdir/results.json")
    st.divider()
    try:
        import ollama
        models = ollama.list().get("models",[])
        st.success(f"Ollama modelleri: {len(models)}")
    except:
        st.warning("Ollama erişilemedi (ollama serve?)")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📋 Planlar")
    plan_path = os.path.join(workdir,"plan.json")
    if os.path.exists(plan_path):
        st.json(json.load(open(plan_path,"r",encoding="utf-8")))
    else:
        st.info("Henüz plan yok.")

with col2:
    st.subheader("📦 Sonuçlar")
    res_path = os.path.join(workdir,"results.json")
    if os.path.exists(res_path):
        data = json.load(open(res_path,"r",encoding="utf-8"))
        st.metric("Görev sayısı", sum(len(w['tasks']) for w in data.get("plan",{}).get("weeks",[])))
        pass_cnt = sum(1 for k,v in data.get("execution",{}).items() if v.get("sandbox_ok"))
        st.metric("Sandbox PASS", pass_cnt)
        with st.expander("Tüm sonuç JSON"):
            st.json(data)
    else:
        st.info("Henüz sonuç yok.")
