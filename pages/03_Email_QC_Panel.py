# pages/03_Email_QC_Panel.py
# SME-only QC panel (no upload/mapping). Admin must pre-load data with fixed headers.

import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
ss = st.session_state

# ---------------------- Session defaults ----------------------
for k, v in {
    "qc_src": pd.DataFrame(),   # Admin must set this before SME uses the page
    "qc_work": pd.DataFrame(),  # Copy of qc_src where QC_TA is written
    "qc_idx": 0,
    "uploaded_name": None,      # Optional: admin can set a friendly file name
}.items():
    if k not in ss:
        ss[k] = v

# ---------------------- Fixed column map (admin responsibility) ----------------------
REQUIRED_COLS = [
    "ID",
    "Question (English)",
    "Options (English)",
    "Answer (English)",
    "Explanation (English)",
    "Question (Tamil)",
    "Options (Tamil)",
    "Answer (Tamil)",
    "Explanation (Tamil)",
    "QC_TA",  # destination for SME edits
]

def _txt(x) -> str:
    if x is None:
        return ""
    s = str(x).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", s).strip()

def split_opts(text: str):
    """Split options into A,B,C,D using tolerant separators."""
    s = _txt(text)
    if not s:
        return ["", "", "", ""]
    s = re.sub(r"\s*(?:^|[|•;])\s*(?:[A-D1-4][\).:-]\s*)", " | ", s)
    parts = re.split(r"\s*\|\s*", s)
    parts = [p.strip(" .;") for p in parts if p.strip()]
    while len(parts) < 4:
        parts.append("")
    return parts[:4]

def build_qc_text(q, a, b, c, d, ans, exp):
    blocks = []
    if q:  blocks.append(f"கேள்வி: {q}")
    opts = [a, b, c, d]
    labels = ["A", "B", "C", "D"]
    opt_str = " | ".join([f"{labels[i]}) {opts[i]}" for i in range(4) if opts[i]])
    if opt_str: blocks.append(f"விருப்பங்கள் (A–D): {opt_str}")
    if ans: blocks.append(f"பதில்: {ans}")
    if exp: blocks.append(f"விளக்கம்: {exp}")
    return "\n\n".join(blocks)

def block(title, body, css):
    st.markdown(
        f"""
        <div class="box {css}">
            <div class="head">{title}</div>
            <div class="body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_en(q, op, ans, exp):
    parts = []
    if q:   parts.append(f"<b>Q:</b> {q}")
    if op:  parts.append(f"<b>Options (A–D):</b> {op}")
    if ans: parts.append(f"<b>Answer:</b> {ans}")
    if exp: parts.append(f"<b>Explanation:</b> {exp}")
    return "<br><br>".join(parts) or "—"

def render_ta(q, op, ans, exp):
    parts = []
    if q:   parts.append(f"<b>கேள்வி:</b> {q}")
    if op:  parts.append(f"<b>விருப்பங்கள் (A–D):</b> {op}")
    if ans: parts.append(f"<b>பதில்:</b> {ans}")
    if exp: parts.append(f"<b>விளக்கம்:</b> {exp}")
    return "<br><br>".join(parts) or "—"

# ---------------------- Admin-prepared data required ----------------------
if ss.qc_src.empty:
    st.markdown("### 📝 SME QC Panel")
    st.info(
        "இந்த பக்கம் ஆசிரியர்களுக்கான எளிய QC திருத்தப் பகுதி. "
        "தரவை **நிர்வாகம் (Admin)** முன்கூட்டியே ஏற்றியிருக்க வேண்டும்.\n\n"
        "Admins: provide a DataFrame in `st.session_state.qc_src` that contains columns:\n"
        f"`{', '.join(REQUIRED_COLS)}`.\n"
        "Once the admin loads it, this page will show the items automatically."
    )
    st.stop()

# Validate required columns once (SME sees a friendly message if admin misconfigured)
missing = [c for c in REQUIRED_COLS if c not in ss.qc_src.columns]
if missing:
    st.error(
        "Admin setup incomplete. Missing columns: " + ", ".join(missing) +
        ". Please ask Admin to fix the source file."
    )
    st.stop()

# Create working copy if needed
if ss.qc_work.empty:
    ss.qc_work = ss.qc_src.copy()

# ---------------------- Top strip (slim) ----------------------
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

hdr_left, hdr_mid, hdr_right = st.columns([2,6,2])
with hdr_left:
    st.markdown("### 📝 SME QC Panel")
    st.caption("English ⇄ Tamil · single-page QC (SME only)")
with hdr_mid:
    st.caption(f"ID: **{rid}** · Row **{ss.qc_idx+1} / {len(ss.qc_work)}**")
    st.progress((ss.qc_idx + 1) / len(ss.qc_work))
with hdr_right:
    cA, cB = st.columns(2)
    with cA:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx <= 0):
            ss.qc_idx = max(0, ss.qc_idx - 1); st.rerun()
    with cB:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx >= len(ss.qc_work) - 1):
            ss.qc_idx = min(len(ss.qc_work) - 1, ss.qc_idx + 1); st.rerun()

st.divider()

# ---------------------- Reference panels ----------------------
en_q   = _txt(row["Question (English)"])
en_op  = _txt(row["Options (English)"])
en_ans = _txt(row["Answer (English)"])
en_exp = _txt(row["Explanation (English)"])

ta_q   = _txt(row["Question (Tamil)"])
ta_op  = _txt(row["Options (Tamil)"])
ta_ans = _txt(row["Answer (Tamil)"])
ta_exp = _txt(row["Explanation (Tamil)"])

block("English Version / ஆங்கிலம்",
      render_en(en_q, en_op, en_ans, en_exp), "en")
block("Tamil Original / தமிழ் மூலப் பதிப்பு",
      render_ta(ta_q, ta_op, ta_ans, ta_exp), "ta")

# ---------------------- SME EDIT CONSOLE ----------------------
st.markdown(
    """<div class="box edit"><div class="head">SME Edit Console / ஆசிரியர் திருத்தம்</div></div>""",
    unsafe_allow_html=True
)

row_key = f"r{ss.qc_idx}"
A, B, C, D = split_opts(ta_op)
defaults = {
    f"q_{row_key}": ta_q,
    f"a_{row_key}": A,
    f"b_{row_key}": B,
    f"c_{row_key}": C,
    f"d_{row_key}": D,
    f"ans_{row_key}": ta_ans,
    f"exp_{row_key}": ta_exp,
}
for k, v in defaults.items():
    if k not in ss:
        ss[k] = v

q_val   = st.text_area("கேள்வி / Question (TA)", value=ss[f"q_{row_key}"], height=90, key=f"q_{row_key}_in")
colA, colB = st.columns(2)
with colA:
    A_val = st.text_input("A", value=ss[f"a_{row_key}"], key=f"a_{row_key}_in")
with colB:
    B_val = st.text_input("B", value=ss[f"b_{row_key}"], key=f"b_{row_key}_in")
colC, colD = st.columns(2)
with colC:
    C_val = st.text_input("C", value=ss[f"c_{row_key}"], key=f"c_{row_key}_in")
with colD:
    D_val = st.text_input("D", value=ss[f"d_{row_key}"], key=f"d_{row_key}_in")
ans_val = st.text_input("பதில்", value=ss[f"ans_{row_key}"], key=f"ans_{row_key}_in")
exp_val = st.text_area("விளக்கம்", value=ss[f"exp_{row_key}"], height=120, key=f"exp_{row_key}_in")

# Live preview
opts_preview = " | ".join([f"A) {A_val}", f"B) {B_val}", f"C) {C_val}", f"D) {D_val}"])
block("Live Preview / நேரடி முன்னோட்டம்",
      render_ta(q_val, opts_preview, ans_val, exp_val), "qc")

# Save buttons
bL, bR = st.columns([1,2])
with bL:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = build_qc_text(q_val, A_val, B_val, C_val, D_val, ans_val, exp_val)
        st.success("Saved.")
with bR:
    if st.button("💾 Save & Next ▶", use_container_width=True, disabled=ss.qc_idx >= len(ss.qc_work) - 1):
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = build_qc_text(q_val, A_val, B_val, C_val, D_val, ans_val, exp_val)
        if ss.qc_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
        st.rerun()

st.caption("SME only edits the bottom console. Admin handles files and headers.")

# ---------------------- Minimal CSS ----------------------
st.markdown("""
<style>
.box{border:1px solid #d9d9d9;border-radius:10px;padding:14px 16px;margin:8px 0}
.box .head{font-weight:700;margin-bottom:8px}
.box.en{background:#e9f3ff;border-color:#a8c8f8}
.box.ta{background:#eaf7ec;border-color:#a9d9b5}
.box.edit{background:#fff4d8;border-color:#ffd27a}
.box.qc{background:#fffbe6;border-color:#ffe58f}
</style>
""", unsafe_allow_html=True)
