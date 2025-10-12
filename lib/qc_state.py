# lib/qc_state.py
import ast
import math
import streamlit as st

# ========= Refined CSS (better spacing, no overlap seams) =========
_LAYOUT_CSS = """
<style>
.block-container {
    padding-top: 12px;
    padding-bottom: 12px;
}
.section {
    border: 2px solid #2f61c1;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 12px;
}
.section.ta { border-color: #2e7d32; }  /* Tamil = green */
.section.en { border-color: #2f61c1; }  /* English = blue */
.section.ed { border-color: #2f61c1; }  /* SME edit = blue */

.section .title {
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 6px;
    line-height: 1.3;
}
.note {
    opacity: 0.65;
    font-size: 13px;
    margin-top: 4px;
}
</style>
"""

# ---------- Helpers ----------
def _section_open(cls: str, title: str) -> None:
    st.markdown(f'<div class="section {cls}"><div class="title">{title}</div>', unsafe_allow_html=True)

def _section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)

def _s(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def _parse_options(val):
    if val is None:
        return []
    if isinstance(val, list):
        return [_s(v) for v in val if _s(v)]
    s = _s(val)
    if not s:
        return []
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list):
            return [_s(v) for v in obj if _s(v)]
    except Exception:
        pass
    parts = [p.strip() for p in (s.split("|") if "|" in s else s.split(","))]
    return [p for p in parts if p]

def _fmt_options(opts):
    if not opts:
        return "—"
    return " | ".join([f"{i}) {o}" for i, o in enumerate(opts, 1)])

# ---------- Column detection ----------
SHORT_EN = ["en.q", "en.o", "en.a", "en.e"]
SHORT_TA = ["ta.q", "ta.o", "ta.a", "ta.e"]
LONG_EN_MAP = {
    "en.q": "question",
    "en.o": "questionOptions",
    "en.a": "answers",
    "en.e": "explanation",
}

def _resolve_column_maps(df):
    cols = set(df.columns)
    en_map, ta_map = {}, {}

    # English
    if all(c in cols for c in SHORT_EN):
        en_map = {c: c for c in SHORT_EN}
    elif all(v in cols for v in LONG_EN_MAP.values()):
        en_map = {k: LONG_EN_MAP[k] for k in SHORT_EN}

    # Tamil
    if all(c in cols for c in SHORT_TA):
        ta_map = {c: c for c in SHORT_TA}

    return en_map, ta_map

def _get_row():
    df = st.session_state.get("qc_df", None)
    if df is None or df.empty:
        return None, {}, {}
    en_map, ta_map = _resolve_column_maps(df)
    idx = int(st.session_state.get("qc_idx", 0))
    if idx < 0 or idx >= len(df):
        idx = 0
        st.session_state["qc_idx"] = idx
    return df.iloc[idx], en_map, ta_map

# ---------- Content rendering ----------
def _editor_tamil():
    st.text_area("", "", height=340, label_visibility="collapsed")

def _render_tamil():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Please upload a bilingual Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not ta_map:
        st.markdown('<div class="note">Tamil columns missing: expected <code>ta.q, ta.o, ta.a, ta.e</code>.</div>', unsafe_allow_html=True)
        return
    q = _s(row[ta_map["ta.q"]])
    o = _fmt_options(_parse_options(row[ta_map["ta.o"]]))
    a = _s(row[ta_map["ta.a"]])
    e = _s(row[ta_map["ta.e"]])
    st.markdown(
        f"**கேள்வி :** {q}\n\n"
        f"**விருப்பங்கள் (A–D) :** {o}\n\n"
        f"**பதில் :** {a}\n\n"
        f"**விளக்கம் :** {e}\n"
    )

def _render_english():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Please upload a bilingual Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not en_map:
        st.markdown('<div class="note">English columns missing: expected <code>en.q, en.o, en.a, en.e</code> or <code>question, questionOptions, answers, explanation</code>.</div>', unsafe_allow_html=True)
        return
    q = _s(row[en_map["en.q"]])
    o = _fmt_options(_parse_options(row[en_map["en.o"]]))
    a = _s(row[en_map["en.a"]])
    e = _s(row[en_map["en.e"]])
    st.markdown(
        f"**Q :** {q}\n\n"
        f"**Options (A–D) :** {o}\n\n"
        f"**Answer :** {a}\n\n"
        f"**Explanation :** {e}\n"
    )

# ---------- Main Layout ----------
def render_reference_and_editor():
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    # 1️⃣ SME EDIT
    _section_open("ed", "SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()

    # 2️⃣ TAMIL REFERENCE
    _section_open("ta", "தமிழ் மூலப் பதிவு")
    _render_tamil()
    _section_close()

    # 3️⃣ ENGLISH REFERENCE
    _section_open("en", "English Version")
    _render_english()
    _section_close()
