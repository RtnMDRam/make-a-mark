# pages/07_English_Tamil_Translator.py
# iPad-friendly 3-panel translator: Top (5%) header+controls, Middle (EN+TA RO),
# Bottom (editable TA: Q, A/B + C/D, Explanation). Headers preserved on export.

import re
import os
import io
import pandas as pd
import streamlit as st

# ---- our shared helpers (already in your repo) ----
from lib import (
    apply_theme,          # Night + compact CSS and tidy headings
    read_bilingual,       # reads .csv/.xlsx with headers
    auto_guess_map,       # guesses "ID, Q_EN, OPT_EN, ANS_EN, EXP_EN, Q_TA, OPT_TA, ANS_TA, EXP_TA"
    ensure_work,          # builds working df with QC_* columns seeded from TA originals
    export_qc             # exports with TA columns replaced by QC_* values; preserves original header names
)

st.set_page_config(page_title="English–Tamil / Translation", page_icon="📝", layout="wide")

# ================= Session =================
ss = st.session_state
for k, v in {
    "night": False,
    "qc_src": pd.DataFrame(),
    "qc_map": {},
    "qc_work": pd.DataFrame(),
    "qc_idx": 0,
    "uploaded_name": None
}.items():
    if k not in ss: ss[k] = v

# ================= Styling =================
apply_theme(ss.night, hide_sidebar=True)  # hide sidebar for SME translators

# ----------------- Small utils -----------------
def _clean(s: str) -> str:
    return str(s or "").replace("\r\n", "\n").strip()

_OPT_PATTERNS = [
    r"(?:^|\s)A\)\s*(.*?)\s+B\)\s*(.*?)\s+C\)\s*(.*?)\s+D\)\s*(.*)$",   # A) B) C) D)
    r"(?:^|\s)A\.\s*(.*?)\s+B\.\s*(.*?)\s+C\.\s*(.*?)\s+D\.\s*(.*)$",   # A. B. C. D.
    r"(?:^|\s)A\s*[:\-]\s*(.*?)\s+B\s*[:\-]\s*(.*?)\s+C\s*[:\-]\s*(.*?)\s+D\s*[:\-]\s*(.*)$",
]
def split_opts(text: str):
    """Best-effort split of options into A,B,C,D."""
    t = " ".join(_clean(text).split())
    # fallback: try pipes or newlines
    pipe = [x.strip() for x in re.split(r"\|+|\n+", t) if x.strip()]
    if len(pipe) == 4:
        return {"A": pipe[0], "B": pipe[1], "C": pipe[2], "D": pipe[3]}
    for pat in _OPT_PATTERNS:
        m = re.search(pat, t, flags=re.IGNORECASE|re.DOTALL)
        if m:
            a,b,c,d = [x.strip() for x in m.groups()]
            return {"A": a, "B": b, "C": c, "D": d}
    # last resort: return whole thing as A
    return {"A": _clean(text), "B": "", "C": "", "D": ""}

def join_opts(ABCD: dict):
    """Join back into a compact canonical string used in export."""
    a = ABCD.get("A","").strip()
    b = ABCD.get("B","").strip()
    c = ABCD.get("C","").strip()
    d = ABCD.get("D","").strip()
    parts = []
    if a: parts.append(f"A) {a}")
    if b: parts.append(f"B) {b}")
    if c: parts.append(f"C) {c}")
    if d: parts.append(f"D) {d}")
    return " | ".join(parts)

def ro_panel(title: str, body: str, color_class: str):
    st.markdown(
        f"<div class='box {color_class}'><h4>{title}</h4>"
        f"<div class='mono'>{_clean(body).replace('\n','<br>')}</div></div>",
        unsafe_allow_html=True
    )

# ================= Top header (≈5%) =================
with st.container():
    c1, c2 = st.columns([4, 3])
    with c1:
        st.markdown(
            "<div style='font-size:1.3rem; font-weight:700;'>English – Tamil / Translation</div>"
            "<div style='margin-top:.15rem; font-size:1.05rem;'>ஆங்கிலம் – தமிழ் / மொழி பெயர்ப்பு</div>",
            unsafe_allow_html=True
        )
    with c2:
        togg_l, togg_r = st.columns([1,1])
        with togg_l:
            ss.night = st.toggle("🌙 Night Mode", value=ss.night)
        with togg_r:
            st.caption("")  # spacing

    # uploader + column mapping (collapsed after first load)
    with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns",
                     expanded=ss.qc_src.empty):
        up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"])
        if up:
            src = read_bilingual(up)
            if src.empty:
                st.error("File appears empty.")
            else:
                ss.uploaded_name = os.path.splitext(up.name)[0]
                ss.qc_src = src
                auto = auto_guess_map(src)
                st.write("**Map the required columns (kept exactly in export):**")
                cols = list(src.columns)

                sel = {}
                L, R = st.columns(2)
                with L:
                    sel["ID"]     = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                    sel["Q_EN"]   = st.selectbox("Question (English)", cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                    sel["OPT_EN"] = st.selectbox("Options (English)", cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                    sel["ANS_EN"] = st.selectbox("Answer (English)", cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                    sel["EXP_EN"] = st.selectbox("Explanation (English)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
                with R:
                    sel["Q_TA"]   = st.selectbox("Question (Tamil)", cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                    sel["OPT_TA"] = st.selectbox("Options (Tamil)", cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                    sel["ANS_TA"] = st.selectbox("Answer (Tamil)", cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                    sel["EXP_TA"] = st.selectbox("Explanation (Tamil)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)

                if st.button("✅ Confirm mapping & start"):
                    ss.qc_map = sel
                    ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)  # seeds QC_* from TA originals
                    ss.qc_idx = 0
                    st.success(f"Loaded {len(ss.qc_work)} rows.")
                    st.rerun()

    # Stop until we have data
    if ss.qc_work.empty:
        st.stop()

    # --- progress + nav + export live in the header strip ---
    row = ss.qc_work.iloc[ss.qc_idx]
    navL, prog, navR = st.columns([2.2, 4, 4])

    with navL:
        idv = row["ID"]
        st.markdown(f"<div class='idtag'>ID: {idv}</div>", unsafe_allow_html=True)
        st.caption(f"Row {ss.qc_idx+1} / {len(ss.qc_work)}")

    with prog:
        st.progress((ss.qc_idx + 1) / len(ss.qc_work))

    with navR:
        n1, n2, n3, n4 = st.columns([1.2, 1.6, 2.0, 1.2])
        with n1:
            if st.button("◀️ Prev", use_container_width=True, disabled=ss.qc_idx <= 0):
                ss.qc_idx = max(0, ss.qc_idx - 1)
                st.rerun()
        with n2:
            # On-demand export buttons (always available)
            xlsx_bytes, csv_bytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
            base = (ss.uploaded_name or "qc_file").replace(".", "_")
            st.download_button("⬇️ Excel", data=xlsx_bytes,
                               file_name=f"{base}_qc_verified.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with n3:
            st.download_button("⬇️ CSV", data=csv_bytes,
                               file_name=f"{base}_qc_verified.csv",
                               mime="text/csv",
                               use_container_width=True)
        with n4:
            if st.button("✅ Complete", use_container_width=True):
                if not xlsx_bytes:
                    st.error("Nothing to export yet.")
                else:
                    st.success("QC file prepared. Use ⬇️ buttons to download.")

st.divider()

# ================= Panel 2: Reference (≈50%) =================
refL, refR = st.columns([1,1])

with refL:
    en = ss.qc_map
    ro_panel("English (Read-only) — Question", ss.qc_work.at[ss.qc_idx, "Q_EN"], "en")
    ro_panel("English — Options", ss.qc_work.at[ss.qc_idx, "OPT_EN"], "en")
    ro_panel("English — Answer", ss.qc_work.at[ss.qc_idx, "ANS_EN"], "en")
    ro_panel("English — Explanation", ss.qc_work.at[ss.qc_idx, "EXP_EN"], "en")

with refR:
    ro_panel("Tamil Original (Read-only) — கேள்வி", ss.qc_work.at[ss.qc_idx, "Q_TA"], "tao")
    ro_panel("Tamil Original — விருப்பங்கள் (A–D)", ss.qc_work.at[ss.qc_idx, "OPT_TA"], "tao")
    ro_panel("Tamil Original — பதில்", ss.qc_work.at[ss.qc_idx, "ANS_TA"], "tao")
    ro_panel("Tamil Original — விளக்கம்", ss.qc_work.at[ss.qc_idx, "EXP_TA"], "tao")

# ================= Panel 3: Editable Console (≈45%) =================
st.markdown("<div class='box edit'><h4>SME Editable Console — ஆசிரியர் திருத்த இடம்</h4></div>", unsafe_allow_html=True)

# 1) Question (Tamil QC)
q_val = st.text_area("கேள்வி", value=_clean(ss.qc_work.at[ss.qc_idx, "QC_Q_TA"]), height=110)

# 2) Options split into A/B (row1) and C/D (row2)
qc_opts = split_opts(ss.qc_work.at[ss.qc_idx, "QC_OPT_TA"])
row1a, row1b = st.columns(2)
with row1a:
    a_val = st.text_area("A", value=qc_opts.get("A",""), height=80)
with row1b:
    b_val = st.text_area("B", value=qc_opts.get("B",""), height=80)
row2c, row2d = st.columns(2)
with row2c:
    c_val = st.text_area("C", value=qc_opts.get("C",""), height=80)
with row2d:
    d_val = st.text_area("D", value=qc_opts.get("D",""), height=80)

# 3) Explanation (Tamil QC)
exp_val = st.text_area("விளக்கம்", value=_clean(ss.qc_work.at[ss.qc_idx, "QC_EXP_TA"]), height=140)

# ---- Buttons row (save + next) ----
bL, bM, bR = st.columns([1.4, 1.8, 6])
with bL:
    if st.button("💾 Save", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, "QC_Q_TA"]   = _clean(q_val)
        ss.qc_work.at[ss.qc_idx, "QC_OPT_TA"] = join_opts({"A":a_val,"B":b_val,"C":c_val,"D":d_val})
        # Keep QC answer synced if it is within A–D; otherwise do not overwrite
        ss.qc_work.at[ss.qc_idx, "QC_EXP_TA"] = _clean(exp_val)
        st.success("Saved (QC columns updated).")
with bM:
    if st.button("💾 Save & Next ▶️", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, "QC_Q_TA"]   = _clean(q_val)
        ss.qc_work.at[ss.qc_idx, "QC_OPT_TA"] = join_opts({"A":a_val,"B":b_val,"C":c_val,"D":d_val})
        ss.qc_work.at[ss.qc_idx, "QC_EXP_TA"] = _clean(exp_val)
        if ss.qc_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
        st.rerun()
with bR:
    st.caption("Tip: Edit all fields, then **Save & Next**. Export buttons are in the top panel.")

# ================= END =================
