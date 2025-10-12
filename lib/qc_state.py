# lib/qc_state.py — larger ref panes, divider above TA, newline cleanup
import ast, math, re
import streamlit as st

# ===== CSS (layout, sizes, dividers) =====
_LAYOUT_CSS = """
<style>
:root{
  /* Height of each reference pane: raise to enlarge TA/EN area. */
  --ref-pane-vh: 24;          /* 24vh + 24vh ≈ 48% of viewport height */
  --divider-top-color: #6bd36b;  /* line between SME editor and TA */
  --divider-mid-color: #5aa3ff;  /* line between TA and EN */
}

.block-container{padding-top:10px;padding-bottom:10px;}

.section{border:0!important;background:transparent!important;margin:0 0 6px 0;padding:0;}
.section .title{font-size:12px;font-weight:700;line-height:1;margin:0 0 4px 0;color:#cfcfcf;}

.content{
  font-size:12px; line-height:1.12;
  padding:0; margin:0;
  max-height: calc(var(--ref-pane-vh) * 1vh);
  overflow:auto;             /* scroll if it exceeds the target height */
  white-space: normal;
  word-break: break-word;
}
.content p, .content ul, .content ol{margin:2px 0 !important;}
.content ul, .content ol{padding-left:16px;margin-left:16px !important;}
.content strong{font-weight:600;}

hr.sme-divider{border:0;height:1px;background:var(--divider-top-color);margin:6px 0;}
hr.ref-divider{border:0;height:1px;background:var(--divider-mid-color);margin:6px 0;}
</style>
"""

# ===== small HTML helpers =====
def _section_open(title:str):
    st.markdown(f'<div class="section"><div class="title">{title}</div>', unsafe_allow_html=True)
def _section_close():
    st.markdown("</div>", unsafe_allow_html=True)

# ===== text helpers =====
def _s(x):
    if x is None: return ""
    if isinstance(x, float) and math.isnan(x): return ""
    return str(x).strip()

def _clean_newlines(s: str) -> str:
    """Make any mixture of real or literal CR/LF sequences read as continuous text."""
    if not s:
        return ""
    # 1) collapse escaped sequences first (e.g., '\\r\\n', '\\n', '\\r')
    s = s.replace("\\r\\n", " ").replace("\\n", " ").replace("\\r", " ")
    # 2) then collapse actual CR/LF characters
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    # 3) squeeze redundant whitespace
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()

def _parse_options(val):
    if val is None: return []
    if isinstance(val, list): return [_s(v) for v in val if _s(v)]
    s = _s(val)
    if not s: return []
    # Try list literal first
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list):
            return [_s(v) for v in obj if _s(v)]
    except Exception:
        pass
    # Otherwise split on | or comma, or labeled numbers like "1) A, 2) B"
    if "|" in s: parts = [p.strip() for p in s.split("|")]
    elif "," in s: parts = [p.strip() for p in s.split(",")]
    else:
        parts = [p.strip(" .)") for p in re.split(r"\d+\)\s*", s) if p.strip()]
    return [p for p in parts if p]

def _fmt_options(opts):
    return "—" if not opts else " | ".join(f"{i}) {o}" for i, o in enumerate(opts, 1))

# ===== column resolution =====
SHORT_EN = ["en.q","en.o","en.a","en.e"]
LONG_EN_MAP = {"en.q":"question","en.o":"questionOptions","en.a":"answers","en.e":"explanation"}
TA_FALLBACKS = {
    "ta.q":["கேள்வி","வினா","தமிழ் கேள்வி"],
    "ta.o":["விருப்பங்கள்","விருப்பங்கள் (A–D)","விருப்பங்கள் (A-D)"],
    "ta.a":["பதில்"],
    "ta.e":["விளக்கம்"],
}

def _resolve_column_maps(df):
    cols = list(df.columns)
    lower = [c.strip().lower() for c in cols]
    en_map, ta_map = {}, {}

    # English: accept short or long names
    if all(c in df.columns for c in SHORT_EN):
        en_map = {c:c for c in SHORT_EN}
    elif all(LONG_EN_MAP[k] in df.columns for k in SHORT_EN):
        en_map = {k:LONG_EN_MAP[k] for k in SHORT_EN}

    # Tamil: fuzzy match common labels
    for key, choices in TA_FALLBACKS.items():
        for label in choices:
            ll = label.strip().lower()
            if ll in lower:
                ta_map[key] = cols[lower.index(ll)]
                break

    return en_map, ta_map

def _get_row():
    df = st.session_state.get("qc_df")
    if df is None or df.empty: return None, {}, {}
    en_map, ta_map = _resolve_column_maps(df)
    idx = int(st.session_state.get("qc_idx", 0))
    if idx < 0 or idx >= len(df):
        idx = 0
        st.session_state["qc_idx"] = idx
    return df.iloc[idx], en_map, ta_map

# ===== section renderers =====
def _editor_tamil():
    st.text_area("", "", height=340, label_visibility="collapsed")

def _render_ta():
    row, _, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="content">Upload a bilingual file and press <b>Load</b>.</div>', unsafe_allow_html=True); return
    if not ta_map:
        st.markdown('<div class="content">Tamil columns not found (கேள்வி / விருப்பங்கள் / பதில் / விளக்கம்).</div>', unsafe_allow_html=True); return

    q = _clean_newlines(_s(row[ta_map["ta.q"]]))
    o = _fmt_options(_parse_options(row[ta_map["ta.o"]]))
    a = _clean_newlines(_s(row[ta_map["ta.a"]]))
    e = _clean_newlines(_s(row[ta_map["ta.e"]]))

    st.markdown(
        f'<div class="content">'
        f'<p><strong>கேள்வி :</strong> {q}</p>'
        f'<p><strong>விருப்பங்கள் (A–D) :</strong> {o}</p>'
        f'<p><strong>பதில் :</strong> {a}</p>'
        f'<p><strong>விளக்கம் :</strong> {e}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

def _render_en():
    row, en_map, _ = _get_row()
    if row is None:
        st.markdown('<div class="content">Upload a bilingual file and press <b>Load</b>.</div>', unsafe_allow_html=True); return
    if not en_map:
        st.markdown('<div class="content">English columns not found.</div>', unsafe_allow_html=True); return

    q = _clean_newlines(_s(row[en_map["en.q"]]))
    o = _fmt_options(_parse_options(row[en_map["en.o"]]))
    a = _clean_newlines(_s(row[en_map["en.a"]]))
    e = _clean_newlines(_s(row[en_map["en.e"]]))

    st.markdown(
        f'<div class="content">'
        f'<p><strong>Q :</strong> {q}</p>'
        f'<p><strong>Options (A–D) :</strong> {o}</p>'
        f'<p><strong>Answer :</strong> {a}</p>'
        f'<p><strong>Explanation :</strong> {e}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ===== public entry point =====
def render_reference_and_editor():
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    # TOP: SME editable (Tamil)
    _section_open("SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()

    # Divider BETWEEN SME editor and Tamil reference (NEW)
    st.markdown('<hr class="sme-divider">', unsafe_allow_html=True)

    # MIDDLE: Tamil reference (larger — height from --ref-pane-vh)
    _section_open("தமிழ் மூலப் பதிவு")
    _render_ta()
    _section_close()

    # Divider between Tamil & English (already present)
    st.markdown('<hr class="ref-divider">', unsafe_allow_html=True)

    # BOTTOM: English reference (larger — same height)
    _section_open("English Version")
    _render_en()
    _section_close()
