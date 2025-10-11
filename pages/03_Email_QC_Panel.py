# pages/03_Email_QC_Panel.py
# SME QC Panel (single-screen, iPad friendly)
# Layout: EN original • TA original • SME Edit Console (Q • A/B/C/D • Answer • Explanation)

import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

ss = st.session_state
# ------------ session defaults ------------
for k, v in {
    "qc_src": pd.DataFrame(),
    "qc_work": pd.DataFrame(),
    "qc_map": {},
    "qc_idx": 0,
    "uploaded_name": None,
}.items():
    if k not in ss:
        ss[k] = v

# ------------ helpers ------------
def _txt(x) -> str:
    if x is None:
        return ""
    s = str(x).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", s).strip()

def split_opts(text: str):
    """Split a single string of options into A,B,C,D using common separators."""
    s = _txt(text)
    if not s:
        return ["", "", "", ""]
    # remove labels like 1), A), 1., A., etc.
    s = re.sub(r"\s*(?:^|[|•;])\s*(?:[A-D1-4][\).:-]\s*)", " | ", s)
    parts = re.split(r"\s*\|\s*", s)
    parts = [p.strip(" .;") for p in parts if p.strip()]
    while len(parts) < 4:
        parts.append("")
    return parts[:4]

def build_qc_text(q, a, b, c, d, ans, exp):
    blocks = []
    if q:  blocks.append(f"கேள்வி: {q}")
    # join options neatly
    opts = [a, b, c, d]
    labels = ["A", "B", "C", "D"]
    opts_str = " | ".join([f"{labels[i]}) {opts[i]}" for i in range(4) if opts[i]])
    if opts_str:
        blocks.append(f"விருப்பங்கள் (A–D): {opts_str}")
    if ans:
        blocks.append(f"பதில்: {ans}")
    if exp:
        blocks.append(f"விளக்கம்: {exp}")
    return "\n\n".join(blocks)

def guess_map(cols):
    """Best-effort mapping by header keywords."""
    C = [c.lower() for c in cols]
    def find(*needles):
        for n in needles:
            for i, c in enumerate(C):
                if n in c:
                    return cols[i]
        return cols[0] if cols else ""
    return {
        "ID":      find("id"),
        "Q_EN":    find("question (en", "q_en", "question en", "question english"),
        "OPT_EN":  find("options (en", "opt_en", "options en"),
        "ANS_EN":  find("answer (en", "ans_en", "answer en"),
        "EXP_EN":  find("explanat", "exp_en"),
        "Q_TA":    find("question (ta", "q_ta", "question tamil", "கேள்வ"),
        "OPT_TA":  find("options (ta", "opt_ta", "விருப்ப"),
        "ANS_TA":  find("answer (ta", "ans_ta", "பதில்"),
        "EXP_TA":  find("explanat", "exp_ta", "விளக்க"),
        "QC_TA":   "QC_TA",
    }

def ensure_qc_work(src: pd.DataFrame, mp: dict) -> pd.DataFrame:
    """Create a working copy with a QC_TA column present."""
    work = src.copy()
    # Add QC_TA if missing; start with Tamil original explanation appended view
    if mp.get("QC_TA") not in work.columns:
        work[mp["QC_TA"]] = ""
    return work

# ------------ upload & mapping (compact) ------------
with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns", expanded=ss.qc_src.empty):
    up = st.file_uploader("Upload bilingual file", type=["csv", "xlsx"], label_visibility="collapsed")
    if up:
        if up.name.lower().endswith(".csv"):
            src = pd.read_csv(up)
        else:
            src = pd.read_excel(up)
        if src.empty:
            st.error("File appears empty.")
        else:
            ss.uploaded_name = up.name.rsplit(".", 1)[0]
            ss.qc_src = src
            # show mapping UI
            cols = list(src.columns)
            auto = guess_map(cols)
            st.caption("Map the required columns (kept exactly in export):")
            c1, c2 = st.columns(2)
            with c1:
                id_col   = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0, key="m_id")
                q_en     = st.selectbox("Question (English)", cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0, key="m_q_en")
                opt_en   = st.selectbox("Options (English)",  cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0, key="m_opt_en")
                ans_en   = st.selectbox("Answer (English)",   cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0, key="m_ans_en")
                exp_en   = st.selectbox("Explanation (English)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0, key="m_exp_en")
            with c2:
                q_ta     = st.selectbox("Question (Tamil)", cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0, key="m_q_ta")
                opt_ta   = st.selectbox("Options (Tamil)",  cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0, key="m_opt_ta")
                ans_ta   = st.selectbox("Answer (Tamil)",   cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0, key="m_ans_ta")
                exp_ta   = st.selectbox("Explanation (Tamil)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0, key="m_exp_ta")
                qc_ta    = st.selectbox("QC Verified (Tamil) — stores SME edits", cols + ["QC_TA"], index=(cols + ["QC_TA"]).index(auto["QC_TA"]) if auto["QC_TA"] in (cols + ["QC_TA"]) else len(cols), key="m_qc_ta")

            if st.button("✅ Confirm mapping & start"):
                ss.qc_map = {
                    "ID": id_col, "Q_EN": q_en, "OPT_EN": opt_en, "ANS_EN": ans_en, "EXP_EN": exp_en,
                    "Q_TA": q_ta, "OPT_TA": opt_ta, "ANS_TA": ans_ta, "EXP_TA": exp_ta, "QC_TA": qc_ta
                }
                ss.qc_work = ensure_qc_work(ss.qc_src, ss.qc_map)
                ss.qc_idx = 0
                st.success(f"Loaded {len(ss.qc_work)} rows.")
                st.rerun()

# stop if nothing loaded yet
if ss.qc_work.empty:
    st.stop()

# ------------ top strip (slim) ------------
row = ss.qc_work.iloc[ss.qc_idx]
rid = row[ss.qc_map["ID"]] if ss.qc_map["ID"] in row else ss.qc_idx + 1
hdr_left, hdr_mid, hdr_right = st.columns([2,6,2])
with hdr_left:
    st.markdown("### 📝 SME QC Panel")
    st.caption("English ⇄ Tamil · single-page QC")
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

# ------------ reference panels ------------
m = ss.qc_map
# English pieces
en_q   = _txt(row.get(m["Q_EN"], ""))
en_op  = _txt(row.get(m["OPT_EN"], ""))
en_ans = _txt(row.get(m["ANS_EN"], ""))
en_exp = _txt(row.get(m["EXP_EN"], ""))

# Tamil pieces
ta_q   = _txt(row.get(m["Q_TA"], ""))
ta_op  = _txt(row.get(m["OPT_TA"], ""))
ta_ans = _txt(row.get(m["ANS_TA"], ""))
ta_exp = _txt(row.get(m["EXP_TA"], ""))

def block(title, body, css):
    st.markdown(
        f"""
        <div class="box {css}">
            <div class="head">{title}</div>
            <div class="body">{body}</div>
        </div>
        """, unsafe_allow_html=True
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

block("English Version / ஆங்கிலம்", render_en(en_q, en_op, en_ans, en_exp), "en")
block("Tamil Original / தமிழ் மூலப் பதிப்பு", render_ta(ta_q, ta_op, ta_ans, ta_exp), "ta")

# ------------ SME EDIT CONSOLE ------------
st.markdown("""<div class="box edit"><div class="head">SME Edit Console / ஆசிரியர் திருத்தம்</div></div>""", unsafe_allow_html=True)

row_key = f"r{ss.qc_idx}"  # stable per row
# initialize per-row default values from Tamil original
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

# inputs (always provide a default so Streamlit doesn't error)
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

# live preview of QC text (mirrors current inputs)
preview = build_qc_text(q_val, A_val, B_val, C_val, D_val, ans_val, exp_val)
block("Live Preview / நேரடி முன்னோட்டம் (QC)", render_ta(q_val, " | ".join([f"A) {A_val}", f"B) {B_val}", f"C) {C_val}", f"D) {D_val}"]), ans_val, exp_val), "qc")

# buttons
bL, bR = st.columns([1,2])
with bL:
    if st.button("💾 Save this row", use_container_width=True):
        # write back to qc_work (QC_TA holds SME-edited text)
        ss.qc_work.at[ss.qc_idx, m["QC_TA"]] = preview
        st.success("Saved.")
with bR:
    if st.button("💾 Save & Next ▶", use_container_width=True, disabled=ss.qc_idx >= len(ss.qc_work) - 1):
        ss.qc_work.at[ss.qc_idx, m["QC_TA"]] = preview
        if ss.qc_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
        st.rerun()

st.divider()
st.caption("Tip: Top two panels are read-only references. Edit only in the SME console. Saving writes to the **QC_TA** column.")

# ------------ minimal CSS ------------
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
