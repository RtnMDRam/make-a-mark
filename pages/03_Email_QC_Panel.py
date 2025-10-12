# pages/03_Email_QC_Panel.py
# SME compact editor (iPad 10.9")
# - Uses lib/top_strip.render_top_strip for the 10% header strip
# - Tight CSS, no bottom slack, compact inputs
# - A,B,C,D on one row; Answer + Glossary compact
# - No yellow "widget key..." banner (we use setdefault + key-only widgets)

from __future__ import annotations
import re
import pandas as pd
import streamlit as st

from lib.top_strip import render_top_strip


# ---------------- page config ----------------
st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------- CSS: compact, hide floating controls, small SME title -----------
st.markdown(
    """
<style>
/* Palm-leaf look is theme background; keep page tight */
main .block-container {padding-top: 8px; padding-bottom: 6px;}
.element-container {margin-bottom: 6px;}
/* remove stray horizontal rules if any */
hr, div[role="separator"]{display:none !important;height:0 !important;margin:0 !important;}

/* Hide Streamlit viewer controls (e.g., 'Manage app') */
header, footer {visibility:hidden; height:0;}
a[aria-label="Manage app"],
button[title="Manage app"],
.viewerBadge_link__1S137, .stDeployButton {display:none !important;}

/* Inputs: slightly smaller type & paddings */
input, textarea {font-size: 16px;}
.stTextInput>div>div, .stTextArea>div>div {padding: 6px 10px;}
.stTextArea textarea {line-height: 1.25;}

/* SME section title smaller */
h3.sme-title {font-size: 18px; margin: 8px 0 6px 0;}
/* Option row tighter */
.optrow {margin-top: 2px; margin-bottom: 4px;}
/* Answer & glossary row */
.ansrow {margin-top: 4px; margin-bottom: 6px;}
/* Explanation box a bit taller but compact */
.expbox .stTextArea>div>div {min-height: 120px;}
/* Subtle label chips */
.labelchip{
  display:inline-block;background:#eef1c8;border-radius:8px;padding:2px 8px;
  font-size:12px;margin-bottom:4px;border:1px solid #d6d7a6;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- helpers ----------------
def _txt(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): 
        return ""
    return str(x).replace("\r\n", "\n").strip()

def _split_opts(opt_text: str):
    """Split 'A) ... | B) ... | C) ... | D) ...' into A,B,C,D (robust for separators | ; • , newlines)."""
    t = _txt(opt_text)
    if not t:
        return ["", "", "", ""]
    # Try labelled A/B/C/D
    m = re.findall(r'[AＤＡA]\)?\s*[:\u0BBE\)]?\s*(.*?)\s*[|•;,\n]+'
                   r'[BＢ]\)?\s*[:\u0BBE\)]?\s*(.*?)\s*[|•;,\n]+'
                   r'[CＣ]\)?\s*[:\u0BBE\)]?\s*(.*?)\s*[|•;,\n]+'
                   r'[DＤ]\)?\s*[:\u0BBE\)]?\s*(.*)', t, flags=re.IGNORECASE|re.S)
    if m:
        a,b,c,d = m[0]
        return [a.strip(), b.strip(), c.strip(), d.strip()]
    # Fallback: split into up to 4 parts
    parts = re.split(r'\s*[|•;,\n]\s*', t)
    parts = [p.strip() for p in parts if p.strip()]
    while len(parts) < 4:
        parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    labels = ["A)","B)","C)","D)"]
    vals = [a,b,c,d]
    out = []
    for i,v in enumerate(vals):
        if _txt(v):
            out.append(f"{labels[i]} {v}")
    return " | ".join(out)

def _load_row(idx: int) -> dict:
    ss = st.session_state
    if "qc_work" not in ss or ss.qc_work.empty:
        return {}
    idx = max(0, min(idx, len(ss.qc_work)-1))
    row = ss.qc_work.iloc[idx]
    # Map expected columns (Tamil)
    q_ta   = _txt(row.get("Question (Tamil)", row.get("Q_TA", "")))
    op_ta  = _txt(row.get("Options (Tamil)", row.get("OPT_TA", "")))
    an_ta  = _txt(row.get("Answer (Tamil)", row.get("ANS_TA", "")))
    ex_ta  = _txt(row.get("Explanation (Tamil)", row.get("EXP_TA", "")))
    A,B,C,D = _split_opts(op_ta)
    return {
        "ID": row.get("ID","—"),
        "Q": q_ta, "A": A, "B": B, "C": C, "D": D,
        "ANS": an_ta, "EXP": ex_ta
    }

def _init_keys_from_row(r: dict):
    """Avoid yellow banner: set defaults once, then use widgets with only key (no value=)."""
    ss = st.session_state
    for k in ["q","oa","ob","oc","od","ans","exp","gloss"]:
        ss.setdefault(k, "")
    ss["q"]   = r.get("Q","")
    ss["oa"]  = r.get("A","")
    ss["ob"]  = r.get("B","")
    ss["oc"]  = r.get("C","")
    ss["od"]  = r.get("D","")
    ss["ans"] = r.get("ANS","")
    ss["exp"] = r.get("EXP","")
    # keep gloss input as user typed; don't overwrite

def _save_current():
    ss = st.session_state
    if "qc_work" not in ss or ss.qc_work.empty:
        return
    i = max(0, min(ss.get("qc_idx",0), len(ss.qc_work)-1))
    df = ss.qc_work
    # Write back into Tamil columns if they exist; else create them.
    for col in ["Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)"]:
        if col not in df.columns:
            df[col] = ""
    df.at[i, "Question (Tamil)"]   = _txt(ss.get("q",""))
    df.at[i, "Options (Tamil)"]    = _join_opts(_txt(ss.get("oa","")), _txt(ss.get("ob","")), _txt(ss.get("oc","")), _txt(ss.get("od","")))
    df.at[i, "Answer (Tamil)"]     = _txt(ss.get("ans",""))
    df.at[i, "Explanation (Tamil)"]= _txt(ss.get("exp",""))
    ss.qc_work = df


# ---------------- handlers wired to top strip ----------------
def _on_save():
    _save_current()
    st.toast("Saved this row.", icon="💾")

def _on_mark_complete():
    _save_current()
    st.toast("Row marked complete (saved).", icon="✅")

def _on_next():
    _save_current()
    ss = st.session_state
    if "qc_idx" not in ss: ss.qc_idx = 0
    ss.qc_idx = min(ss.qc_idx + 1, max(0, len(ss.get("qc_work", pd.DataFrame()))-1))
    st.rerun()


# ---------------- render the top 10% strip ----------------
render_top_strip(
    title_ta="பாட பொருள் நிபுணர் பலகை / SME Panel",
    on_save=_on_save,
    on_mark_complete=_on_mark_complete,
    on_next=_on_next,
)


# ---------------- stop if no data yet ----------------
ss = st.session_state
if "qc_work" not in ss or ss.qc_work.empty:
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()


# ---------------- English / Tamil reference (read-only) ----------------
row = _load_row(ss.get("qc_idx",0))
rid = row.get("ID","—")

def ref_block(title, q, op, ans, exp, cls):
    html = (
        f'<span class="labelchip">{title}</span>'
        f'<div><b>Q:</b> {q}</div>'
        f'<div><b>Options (A–D):</b> {op}</div>'
        f'<div><b>Answer:</b> {ans}</div>'
        f'<div><b>Explanation:</b> {exp}</div>'
    )
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)

# Pull EN/TAMIL strings from df (no edits here; keep as-is)
rdf = ss.qc_work.iloc[ss.qc_idx]
en_q  = _txt(rdf.get("Question (English)",""))
en_op = _txt(rdf.get("Options (English)",""))
en_an = _txt(rdf.get("Answer (English)",""))
en_ex = _txt(rdf.get("Explanation (English)",""))
ta_qr = _txt(rdf.get("Question (Tamil)",""))
ta_opr= _txt(rdf.get("Options (Tamil)",""))
ta_anr= _txt(rdf.get("Answer (Tamil)",""))
ta_exr= _txt(rdf.get("Explanation (Tamil)",""))

ref_block("English Version / ஆங்கிலம்", en_q, en_op, en_an, en_ex, "box en")
ref_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_qr, ta_opr, ta_anr, ta_exr, "box ta")


# ---------------- SME Edit Console ----------------
st.markdown('<h3 class="sme-title">SME Edit Console / ஆசிரியர் திருத்தம்</h3>', unsafe_allow_html=True)

# Initialize state from the current row (prevents yellow banner)
_init_keys_from_row(row)

# Q (2 lines-ish)
q = st.text_area("", key="q", height=72, label_visibility="collapsed",
                 placeholder="கேள்வி / Question (TA)")

# Options row: 4 columns, very tight
st.markdown('<div class="optrow">', unsafe_allow_html=True)
c1,c2,c3,c4 = st.columns([1,1,1,1])
with c1: st.text_input("A", key="oa", label_visibility="collapsed", placeholder="A")
with c2: st.text_input("B", key="ob", label_visibility="collapsed", placeholder="B")
with c3: st.text_input("C", key="oc", label_visibility="collapsed", placeholder="C")
with c4: st.text_input("D", key="od", label_visibility="collapsed", placeholder="D")
st.markdown('</div>', unsafe_allow_html=True)

# Answer + Glossary row
st.markdown('<div class="ansrow">', unsafe_allow_html=True)
ag, an = st.columns([1,1])
with ag:
    st.caption("சொல் அகராதி / Glossary")
    st.text_input("(Type the word)", key="gloss", label_visibility="collapsed",
                  placeholder="Type word")
with an:
    st.caption("பதில் / Answer")
    st.text_input("", key="ans", label_visibility="collapsed",
                  placeholder="A: …")
st.markdown('</div>', unsafe_allow_html=True)

# Explanation
st.caption("விளக்கங்கள் :")
st.markdown('<div class="expbox">', unsafe_allow_html=True)
st.text_area("", key="exp", height=160, label_visibility="collapsed",
             placeholder="விளக்கம் / Explanation")
st.markdown('</div>', unsafe_allow_html=True)
