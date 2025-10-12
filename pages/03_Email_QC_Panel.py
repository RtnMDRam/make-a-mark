# 03_Email_QC_Panel.py
# Standalone page: upload a file, then see Editable Tamil + Tamil/English references.

import streamlit as st
import pandas as pd
import io
import re

# ---------- Page + CSS ----------
st.set_page_config(page_title="SME QC Panel", layout="wide")

st.markdown("""
<style>
/* Hide sidebar + hamburger */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

/* Tighten content width/padding */
.main .block-container { max-width: 1200px; padding: 10px 16px 16px 16px; }

/* Colored separators */
.qc-hr{height:2px;border:0;margin:8px 0 6px;}
.qc-hr.ta{background:#22c55e;}   /* Tamil = green */
.qc-hr.en{background:#3b82f6;}   /* English = blue */

/* Reference panes: top-aligned, exactly 20vh */
.qc-ref{
  height:20dvh; min-height:20vh; max-height:20vh;
  overflow:auto;
  display:flex; flex-direction:column; justify-content:flex-start;
  padding:2px 8px 6px;            /* minimal top padding */
  line-height:1.28; text-align:justify;
  color:#eaeaea;
  font-size:clamp(14px,1.9vh,18px);
}
.qc-ref p{margin:2px 0;}          /* tighter paragraph gaps */

/* Editable box height */
.qc-edit { height:36dvh; min-height:36vh; }

/* Small heading */
.qc-h { font-size:12px; opacity:.95; margin:0 0 2px 0; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def _clean_text(x: str) -> str:
    if x is None:
        return ""
    s = str(x)
    # squash windows newlines that sometimes leak as literal \r\n
    s = s.replace("\\r\\n", " ").replace("\\n", " ").replace("\r\n", " ").replace("\n", " ")
    # collapse extra spaces
    s = re.sub(r"\s{2,}", " ", s).strip()
    # strip stray ** that sneak in
    s = s.replace("**", "")
    return s

def _detect_mapping(cols):
    """Return dict mapping expected keys -> actual column names in the df (case-insensitive)."""
    lc = {c.lower(): c for c in cols}

    # English preferred short keys
    en_map = {
        "en.q": ["en.q", "question", "en_question", "q"],
        "en.o": ["en.o", "questionoptions", "options", "choices", "en_options"],
        "en.a": ["en.a", "answers", "answer", "en_answer"],
        "en.e": ["en.e", "explanation", "en_explanation", "exp"],
    }
    # Tamil preferred keys
    ta_map = {
        "ta.q": ["ta.q", "tamil.q", "ta_question", "tamil_question"],
        "ta.o": ["ta.o", "tamil.o", "ta_options", "tamil_options"],
        "ta.a": ["ta.a", "tamil.a", "ta_answer", "tamil_answer"],
        "ta.e": ["ta.e", "tamil.e", "ta_explanation", "tamil_explanation"],
    }

    mapping = {}
    for key, cands in {**en_map, **ta_map}.items():
        found = None
        for cand in cands:
            if cand.lower() in lc:
                found = lc[cand.lower()]
                break
        mapping[key] = found
    return mapping

def _mk_en(row, m):
    q = _clean_text(row.get(m["en.q"])) if m["en.q"] else ""
    o = _clean_text(row.get(m["en.o"])) if m["en.o"] else ""
    a = _clean_text(row.get(m["en.a"])) if m["en.a"] else ""
    e = _clean_text(row.get(m["en.e"])) if m["en.e"] else ""

    parts = []
    if q:
        parts.append(f"**Q :** {q}")
    if o:
        parts.append(f"**Options (A–D) :** {o}")
    if a:
        parts.append(f"**Answer :** {a}")
    if e:
        parts.append(f"**Explanation :** {e}")
    return "<br/>".join(parts) if parts else "<i>No English content.</i>"

def _mk_ta(row, m):
    q = _clean_text(row.get(m["ta.q"])) if m["ta.q"] else ""
    o = _clean_text(row.get(m["ta.o"])) if m["ta.o"] else ""
    a = _clean_text(row.get(m["ta.a"])) if m["ta.a"] else ""
    e = _clean_text(row.get(m["ta.e"])) if m["ta.e"] else ""

    parts = []
    if q: parts.append(f"**கேள்வி :** {q}")
    if o: parts.append(f"**விருப்பங்கள் (A–D) :** {o}")
    if a: parts.append(f"**பதில் :** {a}")
    if e: parts.append(f"**விளக்கம் :** {e}")
    return "<br/>".join(parts) if parts else "<i>தமிழ் பதிவுகள் இல்லை.</i>"

def _load_file_to_df(uploaded):
    if uploaded is None:
        return None
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    # excel
    data = uploaded.read()
    return pd.read_excel(io.BytesIO(data))

# ---------- Top: upload + load ----------
st.write("")  # small spacer
c1, c2 = st.columns([1, 3])
with c1:
    up = st.file_uploader("Upload the file (Excel/CSV):", type=["xlsx", "xls", "csv"])
with c2:
    if st.button("Load", use_container_width=True):
        df = _load_file_to_df(up)
        if df is None or df.empty:
            st.error("No rows found. Please upload a valid file.")
        else:
            st.session_state.qc_df = df
            st.session_state.qc_map = _detect_mapping(df.columns)
            st.session_state.qc_idx = 0
            st.success("Loaded from file.")

# ---------- If data available, render the layout ----------
df = st.session_state.get("qc_df")
mapping = st.session_state.get("qc_map")
idx = st.session_state.get("qc_idx", 0)

if df is not None:
    # Clamp index
    total = len(df)
    idx = max(0, min(idx, total - 1))
    st.session_state.qc_idx = idx
    row = df.iloc[idx]

    # Nav row
    nc1, nc2, nc3, nc4 = st.columns([1, 1, 3, 1])
    with nc1:
        if st.button("◀︎ Prev", use_container_width=True, disabled=(idx == 0)):
            st.session_state.qc_idx = max(0, idx - 1)
            st.experimental_rerun()
    with nc2:
        if st.button("Next ▶︎", use_container_width=True, disabled=(idx >= total - 1)):
            st.session_state.qc_idx = min(total - 1, idx + 1)
            st.experimental_rerun()
    with nc4:
        st.write(f"Row {idx+1}/{total}")

    # ----- Editable Tamil -----
    st.text_area("Editable Tamil (SME)", key="sme_edit_ta", height=250, placeholder="Type the corrected Tamil here…")

    # ----- Tamil reference (20vh) -----
    st.markdown("<hr class='qc-hr ta'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_mk_ta(row, mapping)}</div>", unsafe_allow_html=True)

    # ----- English reference (20vh) -----
    st.markdown("<hr class='qc-hr en'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_mk_en(row, mapping)}</div>", unsafe_allow_html=True)

else:
    st.info("Please upload a file and press **Load**.")
