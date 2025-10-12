# pages/03_Email_QC_Panel.py
import datetime as dt
import re
from typing import Dict, Any

import pandas as pd
import streamlit as st

# Top bar (date/time + actions + link/upload)
from lib.top_strip import render_top_strip


# ---------- Small CSS: collapse sidebar, trim paddings ----------
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="SME QC Panel")
st.markdown("""
<style>
/* collapse the left sidebar & give us the full width */
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }
.block-container { padding-top: 0.75rem !important; padding-bottom: 1rem !important; }
section.main>div { padding-top: 0.25rem !important; }

/* compact inputs */
.stTextInput, .stTextArea, .stSelectbox { margin-bottom: 0.35rem !important; }

/* card look */
.ref-card {
  border: 1px solid rgba(0,0,0,.1); border-radius: 10px;
  padding: 12px 14px; background: #eef7ed26;
}
.ref-card.en { background: #e8f1ff4d; }   /* English */
.ref-card.ta { background: #eaf7e84d; }   /* Tamil   */

/* section titles */
h3.sme { margin: .2rem 0 .6rem 0 !important; font-size: 1.15rem !important; }
h4.title { margin: .7rem 0 .35rem 0 !important; font-size: 1.05rem !important; }

/* keep the bottom floating Streamlit "Manage app" out of sight for SMEs */
button[aria-label="Manage app"] { display:none !important; }
</style>
""", unsafe_allow_html=True)


# ---------- helpers ----------
def _get_ss(name: str, default=None):
    return st.session_state.get(name, default)


def _df_ready() -> bool:
    """True when top strip has published qc_df and qc_idx."""
    return isinstance(_get_ss("qc_df"), pd.DataFrame) and isinstance(_get_ss("qc_idx"), int)


def _row() -> Dict[str, Any]:
    """Current row as a dict; safe on bounds."""
    df: pd.DataFrame = _get_ss("qc_df")
    idx: int = _get_ss("qc_idx", 0)
    if df is None or len(df) == 0:
        return {}
    idx = max(0, min(idx, len(df) - 1))
    rec = df.iloc[idx]
    if isinstance(rec, pd.Series):
        return rec.to_dict()
    return dict(rec)


def _guess(field_map: Dict[str, str], rec: Dict[str, Any]) -> Dict[str, str]:
    """
    Tries to find sensible text for each logical field even if column names differ.
    field_map keys: q_ta, a_ta, b_ta, c_ta, d_ta, ans_ta, exp_ta, q_en, a_en, b_en, c_en, d_en, ans_en, exp_en
    """
    out = {k: "" for k in field_map.keys()}
    if not rec:
        return out

    # direct matches first
    for k, col in field_map.items():
        if col and col in rec and pd.notna(rec[col]):
            out[k] = str(rec[col]).strip()

    # fallbacks by pattern
    def pick(regexes, exclude=()):
        for col in rec.keys():
            if col in exclude: 
                continue
            name = str(col).lower()
            for rg in regexes:
                if re.search(rg, name):
                    val = rec[col]
                    if pd.notna(val):
                        return str(val).strip()
        return ""

    # Tamil
    out["q_ta"]   = out["q_ta"] or pick([r"^q.*ta", r"^question.*ta", r"^q(_|-)\s*tamil", r"tamil.*q"])
    out["a_ta"]   = out["a_ta"] or pick([r"(^a$|^opt[_-]?a)", r"^choice[_-]?a"])
    out["b_ta"]   = out["b_ta"] or pick([r"(^b$|^opt[_-]?b)", r"^choice[_-]?b"])
    out["c_ta"]   = out["c_ta"] or pick([r"(^c$|^opt[_-]?c)", r"^choice[_-]?c"])
    out["d_ta"]   = out["d_ta"] or pick([r"(^d$|^opt[_-]?d)", r"^choice[_-]?d"])
    out["ans_ta"] = out["ans_ta"] or pick([r"^ans.*ta", r"^answer.*ta", r"tamil.*ans"])
    out["exp_ta"] = out["exp_ta"] or pick([r"^exp.*ta", r"^expla.*ta", r"tamil.*exp"])

    # English
    out["q_en"]   = out["q_en"] or pick([r"^q($|.*en)", r"^question($|.*en)", r"english.*q"])
    out["a_en"]   = out["a_en"] or pick([r"(^a$|^opt[_-]?a)", r"^choice[_-]?a"])
    out["b_en"]   = out["b_en"] or pick([r"(^b$|^opt[_-]?b)", r"^choice[_-]?b"])
    out["c_en"]   = out["c_en"] or pick([r"(^c$|^opt[_-]?c)", r"^choice[_-]?c"])
    out["d_en"]   = out["d_en"] or pick([r"(^d$|^opt[_-]?d)", r"^choice[_-]?d"])
    out["ans_en"] = out["ans_en"] or pick([r"^ans($|.*en)", r"^answer($|.*en)", r"english.*ans"])
    out["exp_en"] = out["exp_en"] or pick([r"^exp($|.*en)", r"^expla($|.*en)", r"english.*exp"])

    return out


def _render_ref_card(title: str, cls: str, q: str, a: str, b: str, c: str, d: str, ans: str, exp: str):
    st.markdown(f'<h4 class="title">{title}</h4>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f"""
<div class="ref-card {cls}">
<b>Q:</b> {st.escape_markdown(q) if q else "—"}  
<b>Options (A–D):</b> {st.escape_markdown(a) if a else "—"} | {st.escape_markdown(b) if b else "—"} | {st.escape_markdown(c) if c else "—"} | {st.escape_markdown(d) if d else "—"}  
<b>Answer:</b> {st.escape_markdown(ans) if ans else "—"}  
<b>Explanation:</b> {st.escape_markdown(exp) if exp else "—"}
</div>
""",
            unsafe_allow_html=True,
        )


# ---------- page body ----------
ready = render_top_strip()  # shows top bar & publishes st.session_state.qc_df / qc_idx

if not _df_ready():
    # short nudge until a file/link is loaded
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()

# We have a dataset row
rec = _row()

# Map your usual column names here (leave "" to auto-guess):
FIELD_MAP = dict(
    q_ta="q_ta", a_ta="A_ta", b_ta="B_ta", c_ta="C_ta", d_ta="D_ta", ans_ta="ans_ta", exp_ta="exp_ta",
    q_en="q_en", a_en="A_en", b_en="B_en", c_en="C_en", d_en="D_en", ans_en="ans_en", exp_en="exp_en",
)
G = _guess(FIELD_MAP, rec)

# ---------- ORDER YOU ASKED: 1) Editor, 2) Tamil, 3) English ----------

# 1) SME EDIT CONSOLE – TOP
st.markdown('<h3 class="sme">SME Edit Console / ஆசிரியர் திருத்தம்</h3>', unsafe_allow_html=True)
with st.container():
    # Question + Answer + Explanation (editable)
    cQ, cAns = st.columns([2, 1])
    q_key  = "sme_q_ta"
    a_key  = "sme_ans_ta"
    e_key  = "sme_exp_ta"
    q_val  = st.session_state.get(q_key, G["q_ta"])
    ansVal = st.session_state.get(a_key, G["ans_ta"])
    expVal = st.session_state.get(e_key, G["exp_ta"])

    with cQ:
        q_new = st.text_area(" ", value=q_val or "", height=90, key=q_key)
    with cAns:
        ans_new = st.text_input(" பதில் / Answer", value=ansVal or "", key=a_key)

    cA, cB = st.columns(2)
    with cA:
        optA = st.text_input("A", value=G["a_ta"])
    with cB:
        optB = st.text_input("B", value=G["b_ta"])

    cC, cD = st.columns(2)
    with cC:
        optC = st.text_input("C", value=G["c_ta"])
    with cD:
        optD = st.text_input("D", value=G["d_ta"])

    st.text_area(" விளக்கங்கள் :", value=expVal or "", height=110, key=e_key)

# spacer between editor and references
st.divider()

# 2) TAMIL ORIGINAL – MIDDLE
_render_ref_card(
    "Tamil Original / தமிழ் மூலப் பதிப்பு", "ta",
    q=G["q_ta"], a=G["a_ta"], b=G["b_ta"], c=G["c_ta"], d=G["d_ta"],
    ans=G["ans_ta"], exp=G["exp_ta"]
)

st.markdown("")

# 3) ENGLISH – BOTTOM
_render_ref_card(
    "English Version / ஆங்கிலம்", "en",
    q=G["q_en"], a=G["a_en"], b=G["b_en"], c=G["c_en"], d=G["d_en"],
    ans=G["ans_en"], exp=G["exp_en"]
)
