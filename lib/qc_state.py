# lib/qc_state.py
import ast
import math
import re
import streamlit as st

# ================= CLEAN LAYOUT (no color borders, soft box spacing) =================
_LAYOUT_CSS = """
<style>
.block-container{padding-top:12px;padding-bottom:12px;}
.section{
    border:1px solid #333;
    border-radius:10px;
    padding:16px 18px;
    margin-top:16px;
    background-color:rgba(255,255,255,0.02);
}
.section .title{
    font-size:13px;
    font-weight:700;
    margin-bottom:6px;
    line-height:1.25;
    color:#ccc;
}
.note{
    opacity:.7;
    font-size:13px;
    margin:2px 0 2px;
}
</style>
"""

def _section_open(title: str) -> None:
    st.markdown(f'<div class="section"><div class="title">{title}</div>', unsafe_allow_html=True)

def _section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)

def _s(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def _clean_newlines(s: str) -> str:
    if not s:
        return s
    s = s.replace("\\r\\n", "\n").replace("\\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s

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
    if "|" in s:
        parts = [p.strip() for p in s.split("|")]
    elif "," in s:
        parts = [p.strip() for p in s.split(",")]
    else:
        parts = [p.strip(" .)") for p in re.split(r"\d+\\)\s*", s) if p.strip()]
    return [p for p in parts if p]

def _fmt_options(opts):
    if not opts:
        return "—"
    return " | ".join(f"{i}) {o}" for i, o in enumerate(opts, 1))

# ---- column matching ----
SHORT_EN = ["en.q", "en.o", "en.a", "en.e"]
SHORT_TA = ["ta.q", "ta.o", "ta.a", "ta.e"]
LONG_EN_MAP = {
    "en.q": "question",
    "en.o": "questionOptions",
    "en.a": "answers",
    "en.e": "explanation",
}
TA_FALLBACKS = {
    "ta.q": ["கேள்வி", "வினா", "தமிழ் கேள்வி"],
    "ta.o": ["விருப்பங்கள்", "விருப்பங்கள் (A–D)", "விருப்பங்கள் (A-D)"],
    "ta.a": ["பதில்"],
    "ta.e": ["விளக்கம்"],
}

def _norm(s): return s.strip().lower()

def _resolve_column_maps(df):
    cols = list(df.columns)
    norm_cols = [_norm(c) for c in cols]
    en_map = {}
    ta_map = {}

    if all(c in df.columns for c in SHORT_EN):
        en_map = {c: c for c in SHORT_EN}
    elif all(v in df.columns for v in LONG_EN_MAP.values()):
        en_map = {k: LONG_EN_MAP[k] for k in SHORT_EN}

    for k, patterns in TA_FALLBACKS.items():
        for pat in patterns:
            for i, nc in enumerate(norm_cols):
                if _norm(pat) in nc:
                    ta_map[k] = cols[i]
                    break
            if k in ta_map:
                break
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

# ---- section renderers ----
def _editor_tamil():
    st.text_area("", "", height=340, label_visibility="collapsed")

def _render_ta_box():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Upload a bilingual Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not ta_map:
        st.markdown('<div class="note">Tamil columns not found (கேள்வி / விருப்பங்கள் / பதில் / விளக்கம்).</div>', unsafe_allow_html=True)
        return
    q = _clean_newlines(_s(row[ta_map["ta.q"]]))
    o = _fmt_options(_parse_options(row[ta_map["ta.o"]]))
    a = _clean_newlines(_s(row[ta_map["ta.a"]]))
    e = _clean_newlines(_s(row[ta_map["ta.e"]]))
    st.markdown(f"**கேள்வி :** {q}\n\n**விருப்பங்கள் (A–D) :** {o}\n\n**பதில் :** {a}\n\n**விளக்கம் :** {e}\n")

def _render_en_box():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Upload a bilingual Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not en_map:
        st.markdown('<div class="note">English columns not found.</div>', unsafe_allow_html=True)
        return
    q = _clean_newlines(_s(row[en_map["en.q"]]))
    o = _fmt_options(_parse_options(row[en_map["en.o"]]))
    a = _clean_newlines(_s(row[en_map["en.a"]]))
    e = _clean_newlines(_s(row[en_map["en.e"]]))
    st.markdown(f"**Q :** {q}\n\n**Options (A–D) :** {o}\n\n**Answer :** {a}\n\n**Explanation :** {e}\n")

# ---- layout ----
def render_reference_and_editor():
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    _section_open("SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()
    _section_open("தமிழ் மூலப் பதிவு")
    _render_ta_box()
    _section_close()
    _section_open("English Version")
    _render_en_box()
    _section_close()
