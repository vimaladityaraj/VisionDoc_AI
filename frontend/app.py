"""Streamlit frontend for VisionDoc AI."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import requests
import streamlit as st
from dotenv import dotenv_values

cfg = dotenv_values(".env")
API_BASE = cfg.get("API_BASE_URL", "http://localhost:8001")

st.set_page_config(
    page_title="VisionDoc AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --bg: #0b1020;
  --panel: #111827;
  --panel-2: #151f32;
  --border: #26364f;
  --text: #f8fafc;
  --muted: #94a3b8;
  --accent: #7c9cff;
  --accent-2: #22c55e;
  --warn: #f59e0b;
}
.block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1220px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #0b1020 0%, #111827 100%);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color: var(--muted);}
.hero {
  background: radial-gradient(circle at top left, rgba(124,156,255,0.35), transparent 28%),
              linear-gradient(135deg, #121a2e 0%, #17233c 55%, #0e172a 100%);
  border: 1px solid var(--border);
  border-radius: 26px;
  padding: 32px 34px;
  box-shadow: 0 18px 60px rgba(0,0,0,0.25);
  margin-bottom: 22px;
}
.hero h1 {font-size: 46px; line-height: 1.05; margin: 0 0 10px 0; letter-spacing: -0.04em;}
.hero p {font-size: 16px; color: #cbd5e1; margin: 0 0 18px 0; max-width: 850px;}
.badge {
  display:inline-block; padding: 7px 12px; border-radius: 999px; border:1px solid #334155;
  margin: 5px 7px 0 0; font-size:12px; color:#dbeafe; background:rgba(15,23,42,0.75);
}
.metric-card, .card {
  background: linear-gradient(180deg, rgba(17,24,39,0.98), rgba(15,23,42,0.98));
  border:1px solid var(--border); border-radius:20px; padding:20px; margin:12px 0;
  box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.empty-card {
  text-align:center; padding:72px 30px; border:1px dashed #334155; border-radius:22px;
  background:rgba(17,24,39,0.55); margin-top:16px;
}
.empty-card h2 {margin-bottom:8px; letter-spacing:-0.02em;}
.empty-card p {color: var(--muted); max-width: 680px; margin: 0 auto;}
.field-card {
  background:#0c1324; border:1px solid #27364f; border-radius:14px; padding:14px 15px; margin:10px 0;
}
.field-card .key {color:#bfdbfe; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;}
.field-card code {white-space:pre-wrap; color:#e2e8f0; font-size:13px;}
.successbox, .warnbox, .infobox {padding:14px 15px; border-radius:14px; margin:10px 0;}
.successbox {background:rgba(34,197,94,.12); border:1px solid rgba(34,197,94,.5); color:#dcfce7;}
.warnbox {background:rgba(245,158,11,.12); border:1px solid rgba(245,158,11,.5); color:#fef3c7;}
.infobox {background:rgba(124,156,255,.12); border:1px solid rgba(124,156,255,.45); color:#dbeafe;}
.small-label {font-size:12px; color:var(--muted); margin-bottom:5px;}
.footer-note {color:var(--muted); font-size:13px; text-align:center; margin-top:28px;}
.stButton > button {border-radius: 12px; font-weight: 700;}
[data-testid="stFileUploader"] {background:#0c1324; border:1px solid #27364f; border-radius:16px; padding:12px;}
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path: str, timeout: int = 5) -> Any:
    response = requests.get(f"{API_BASE}{path}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def render_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None or value == "":
        return "null"
    return str(value)


def flatten_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in fields.items()}


if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.markdown("### 📄 VisionDoc AI")
    st.caption("Document intelligence with OCR + local LLM extraction")
    st.divider()

    st.markdown("#### Upload")
    uploaded = st.file_uploader(
        "Choose a PDF or image",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"],
        help="Works best with clear invoices, receipts, forms, and scanned business documents.",
    )

    analyze = st.button("Analyze Document", type="primary", use_container_width=True)

    st.divider()
    st.markdown("#### System Status")
    try:
        health = api_get("/health/", timeout=3)
        st.success(f"Online · {health['provider']} / {health['model']}")
    except Exception:
        st.error("Backend offline")
        st.caption("Start FastAPI on port 8001 and refresh this page.")

    st.divider()
    st.markdown("#### Recent Analyses")
    try:
        docs = api_get("/documents/", timeout=5)
        if docs:
            for item in docs[:8]:
                st.caption(f"{item.get('document_type', 'unknown')} · {item.get('filename', '')}")
        else:
            st.caption("No saved analyses yet.")
    except Exception:
        st.caption("History unavailable.")

st.markdown(
    """
<div class="hero">
  <h1>VisionDoc AI</h1>
  <p>Convert invoices, receipts, forms, and scanned documents into validated structured JSON using OCR, document classification, and local LLM extraction.</p>
  <span class="badge">FastAPI backend</span>
  <span class="badge">Streamlit interface</span>
  <span class="badge">PyMuPDF + Tesseract OCR</span>
  <span class="badge">Ollama / Qwen3</span>
  <span class="badge">JSON + CSV export</span>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown('<div class="metric-card"><div class="small-label">Input Types</div><h3>PDF + 6 Image Formats</h3></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><div class="small-label">Extraction Output</div><h3>Structured JSON</h3></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="small-label">Deployment Mode</div><h3>Local-first AI</h3></div>', unsafe_allow_html=True)

if analyze:
    if uploaded is None:
        st.warning("Upload a document first.")
    else:
        with st.spinner("Running OCR, classifying document type, and extracting fields..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            try:
                response = requests.post(f"{API_BASE}/documents/analyze", files=files, timeout=240)
                if response.status_code != 200:
                    st.error(response.text)
                else:
                    st.session_state.result = response.json()["document"]
                    st.toast("Document analyzed successfully", icon="✅")
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

if st.session_state.result is None:
    st.markdown(
        """
<div class="empty-card">
  <h2>Upload a document to begin</h2>
  <p>VisionDoc AI will extract OCR text, classify the document, identify key business fields, validate totals when possible, and generate downloadable JSON/CSV outputs.</p>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    doc = st.session_state.result
    fields = doc.get("fields", {}) or {}
    validation = doc.get("validation", []) or []

    st.markdown(
        f"""
<div class="card">
  <div class="small-label">Analyzed Document</div>
  <h2 style="margin-top:0;">{doc.get('filename', 'Document')}</h2>
  <span class="badge">Type: {doc.get('document_type', 'unknown')}</span>
  <span class="badge">ID: {doc.get('document_id', '')[:8]}...</span>
  <span class="badge">Fields: {len(fields)}</span>
</div>
""",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([0.58, 0.42])

    with col_left:
        st.markdown("### Extracted Fields")
        if fields:
            for key, value in fields.items():
                st.markdown(
                    f"""
<div class="field-card">
  <div class="key">{key.replace('_', ' ')}</div>
  <code>{render_value(value)}</code>
</div>
""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No fields were extracted.")

        json_payload = json.dumps(doc, indent=2, ensure_ascii=False)
        csv_payload = pd.DataFrame([flatten_fields(fields)]).to_csv(index=False)

        download_col1, download_col2 = st.columns(2)
        with download_col1:
            st.download_button(
                "Download JSON",
                data=json_payload,
                file_name=f"{doc.get('document_id', 'visiondoc')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with download_col2:
            st.download_button(
                "Download CSV",
                data=csv_payload,
                file_name=f"{doc.get('document_id', 'visiondoc')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_right:
        st.markdown("### Validation & Evidence")
        if validation:
            for note in validation:
                icon = "✅" if "passed" in note.lower() else "⚠️"
                box = "successbox" if icon == "✅" else "warnbox"
                st.markdown(f'<div class="{box}">{icon} {note}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="successbox">✅ No validation warnings found.</div>', unsafe_allow_html=True)

        st.markdown('<div class="infobox">Tip: Use clear scans and documents with visible totals, dates, and issuer names for best extraction quality.</div>', unsafe_allow_html=True)

        with st.expander("Raw OCR Text", expanded=False):
            st.text_area("OCR output", doc.get("raw_text", ""), height=360)

st.markdown(
    '<div class="footer-note">Powered by FastAPI, Streamlit, PyMuPDF, Tesseract OCR, Ollama, and local-first document processing.</div>',
    unsafe_allow_html=True,
)
