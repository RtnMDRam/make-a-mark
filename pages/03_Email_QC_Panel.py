# pages/03_Email_QC_Panel.py
# SME compact editor — 6 rows, tight grid, top glossary drawer, no bottom slack

import io, re
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ---------------- CSS: compact page & inputs ----------------
st.markdown("""
<style>
/* Hide sidebar & chrome for SME view */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"]{visibility:hidden;height:0;}
main .block-container{padding:8px 10px 4px;}
.element-container{margin-bottom:6px;}
hr, div[role="separator"]{display:none !important;height:0 !important;margin:0 !important;}
input, textarea{font-size:16px;}
.q-2line textarea{height:64px !important;}            /* ~2 lines */
.optrow [data-testid="column"]{padding-right:6px;}
.optrow .element-container{margin-bottom:4px;}
.answrap > div > div{border:1px solid #b5b5b5 !important;border-radius:8px !important;}
.btnrow{margin-top:6px;}

/* Reference panels */
.box{border:1px solid #d9d9d9;border-radius:12px;padding:10px 12px;margin:8px 0;}
.box.en{background:#eef6ff;border-color:#c9e0ff;}
.box.ta{background:#eff9ef;border-color:#bde5c0;}
.label{display:inline-block;background:#e7effc;color:#11365a;padding:2px 8px;border-radius:8px;font-size:.92rem;}

/* Top bar chips (right) */
.topbar{background:#0e1116;border-radius:8px;padding:6px 10px;color:#fff;}
.chips{display:flex;gap:8px;justify-content:flex-end;align-items:center;}
.chip{background:#1b2230;color:#cfe3ff;padding:3px 8px;border-radius:999px;font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ---------------- helpers ----------------
REQ_COLS = [
    "ID",
    "Question (English)","Options (English)","Answer (English)","Explanation (English)",
    "Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)",
    "QC_TA"
]

def _txt(v): 
    if pd.isna(v): return ""
    return str(v).replace("\\r\\n","\n").replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return "","","",""
    parts = re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts = [p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q):   out.append(f"Q: {_txt(q)}")
    opts=[x for x in (_txt(a),_txt(b),_txt(c),_txt(d)) if x]
    if opts:      out.append("Options (A–D): " + " | ".join([f"{lab}) {opt}" for lab,opt in zip(["A","B","C","D"],opts)]))
    if _txt(ans): out.append(f"Answer: {_txt(ans)}")
    if _txt(exp): out.append(f"Explanation: {_txt(exp)}")
    return "\n".join(out)

def _clean_drive(url:str)->str:
    if "drive.google.com" not in url: return url
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def read_from_link(url:str)->pd.DataFrame:
    url=_clean_drive(url.strip())
    try:
        return pd.read_csv(url)
    except Exception: ...
    try:
        return pd.read_excel(url)
    except Exception as e:
        raise RuntimeError(f"Could not open link. Expecting CSV/XLSX. Details: {e}")

def normalize_columns(df:pd.DataFrame)->pd.DataFrame:
    cols_lower = {c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map = {
        "ID"                    : pick("ID","Id","id"),
        "Question (English)"    : pick("Question (English)","Q_EN","Question_English"),
        "Options (English)"     : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"      : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)" : pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"      : pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"       : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"        : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)"   : pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"                 : pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
    }
    out=pd.DataFrame()
    for k,src in col_map.items():
        if src is None:
            if k=="QC_TA":
                out[k]=""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k]=df[src]
    return out.reset_index(drop=True)

def apply_subset(df:pd.DataFrame)->pd.DataFrame:
    # support deep-links: ?ids=1,2 or ?rows=11-25
    try: qp = st.query_params
    except Exception: qp = {}
    ids  = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        id_list = re.split(r"[,\\s]+", ids[0].strip())
        id_list = [x for x in id_list if x!=""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\\s*(\\d+)\\s*-\\s*(\\d+)\\s*$", rows[0])
        if m:
            a,b=int(m.group(1)),int(m.group(2))
            a,b = min(a,b), max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

def glossary_drawer(show:bool, query:str=""):
    """Top pop-down drawer. Toggle with show=True/False."""
    if not show: return
    with st.expander("📚 Vocabulary / களஞ்சியம்", expanded=True):
        c1,c2,c3 = st.columns([6,1,1])
        with c1: st.caption(f"Results for: — {query or '—'}")
        with c2:
            st.button("+ Add entry", use_container_width=True, key="add_entry_stub")
        with c3:
            if st.button("✕ Close", use_container_width=True, key="close_gloss"):
                st.session_state["show_gloss"]=False
        st.info("No matches yet. Hook to your glossary CSV/Drive later.")

# ---------------- session init ----------------
ss = st.session_state
for k,v in (("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),
            ("link_in",""),("show_gloss",False),("gloss_query","")):
    if k not in ss: ss[k]=v

# ---------------- deep-link auto load (optional) ----------------
try:
    qp = st.query_params
except Exception:
    qp = {}
auto_file = qp.get("file", [])
if auto_file and ss.qc_work.empty:
    try:
        df = read_from_link(auto_file[0])
        df = normalize_columns(df)
        df = apply_subset(df)
        if "QC_TA" not in df.columns: df["QC_TA"]=""
        ss.qc_src = df.copy(); ss.qc_work = df.copy(); ss.qc_idx = 0
    except Exception as e:
        st.error(str(e))

# ---------------- Admin loader (only when empty) ----------------
if ss.qc_work.empty:
    st.markdown("### 📝 SME QC Panel")
    st.info("Paste the CSV/XLSX link sent by Admin, or upload the file.")
    c1,c2,c3 = st.columns([4,2,1])
    with c1:
        upl = st.file_uploader("Upload file (CSV/XLSX)", type=["csv","xlsx"])
    with c2:
        ss.link_in = st.text_input("…or paste link (CSV/XLSX/Drive)", value=ss.link_in)
    with c3:
        if st.button("Load", use_container_width=True):
            try:
                if upl is not None:
                    df = pd.read_csv(upl) if upl.name.lower().endswith(".csv") else pd.read_excel(upl)
                else:
                    if not ss.link_in.strip(): 
                        raise RuntimeError("Upload a file or paste a link.")
                    df = read_from_link(ss.link_in)
                df = normalize_columns(df)
                df = apply_subset(df)
                if "QC_TA" not in df.columns: df["QC_TA"]=""
                ss.qc_src = df.copy(); ss.qc_work = df.copy(); ss.qc_idx = 0
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.stop()

# ---------------- Top status ----------------
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]
total = len(ss.qc_work)
cur   = ss.qc_idx + 1
time_24h = datetime.now().strftime("%H:%M")

cL, cMid, cR = st.columns([2,6,2])
with cL:  st.markdown("### 📝 SME QC Panel")
with cMid: st.progress(cur/max(1,total))
with cR:
    st.markdown(
        f"""
        <div class='topbar'>
          <div class='chips'>
            <span class='chip'>Row {cur}</span>
            <span class='chip'>ID: {rid}</span>
            <span class='chip'>of {total}</span>
            <span class='chip'>{time_24h}</span>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

cPrev, cSpacer, cNext = st.columns([1,8,1])
with cPrev:
    if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
        ss.qc_idx -= 1; st.rerun()
with cNext:
    if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=total-1):
        ss.qc_idx += 1; st.rerun()

# ---------------- Reference panels ----------------
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br>"
        f"<b>Q:</b> {_txt(q)}<br>"
        f"<b>Options (A–D):</b> {_txt(op)}<br>"
        f"<b>Answer:</b> {_txt(ans)}<br>"
        f"<b>Explanation:</b> {_txt(exp)}"
    )
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

en_q, en_op, en_ans, en_exp = [row[c] for c in ("Question (English)","Options (English)","Answer (English)","Explanation (English)")]
ta_q, ta_op, ta_ans, ta_exp = [row[c] for c in ("Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)")]

view_block("English Version / ஆங்கிலம்", en_q, en_op, en_ans, en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q, ta_op, ta_ans, ta_exp, "ta")

# ---------------- Glossary drawer (top pop-down) ----------------
glossary_drawer(ss.get("show_gloss", False), ss.get("gloss_query",""))

# ---------------- SME Edit Console (6 compact rows) ----------------
st.subheader("SME Edit Console / ஆசிரியர் திருத்தம்")

A,B,C,D = _split_opts(ta_op)
rk = f"r{ss.qc_idx}"

# 1) Question (~2 lines)
q = st.text_area(" ", value=ss.get(f"q_in_{rk}", _txt(ta_q)), key=f"q_in_{rk}",
                 label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")
st.markdown("<div class='q-2line'></div>", unsafe_allow_html=True)

# 2) Options grid (A,B)
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
r1c1, r1c2 = st.columns(2)
with r1c1:
    a = st.text_input(" ", value=ss.get(f"a_in_{rk}", _txt(A)), key=f"a_in_{rk}",
                      label_visibility="collapsed", placeholder="A")
with r1c2:
    b = st.text_input(" ", value=ss.get(f"b_in_{rk}", _txt(B)), key=f"b_in_{rk}",
                      label_visibility="collapsed", placeholder="B")

# 3) Options grid (C,D)
r2c1, r2c2 = st.columns(2)
with r2c1:
    c = st.text_input(" ", value=ss.get(f"c_in_{rk}", _txt(C)), key=f"c_in_{rk}",
                      label_visibility="collapsed", placeholder="C")
with r2c2:
    d = st.text_input(" ", value=ss.get(f"d_in_{rk}", _txt(D)), key=f"d_in_{rk}",
                      label_visibility="collapsed", placeholder="D")
st.markdown("</div>", unsafe_allow_html=True)

# 4) Tiny row: left = Go + word (opens top drawer); right = Answer
gL, gR = st.columns([1,1])
with gL:
    gl, gi = st.columns([1,5])
    with gl:
        if st.button("Go", use_container_width=True, key=f"go_{rk}"):
            ss["gloss_query"] = ss.get(f"gloss_q_{rk}","")
            ss["show_gloss"] = True
            st.rerun()
    with gi:
        st.text_input("Groceries / Vocabulary", key=f"gloss_q_{rk}",
                      placeholder="Type word", label_visibility="collapsed")
with gR:
    st.text_input("பதில் / Answer", value=ss.get(f"ans_in_{rk}", _txt(ta_ans)),
                  key=f"ans_in_{rk}", label_visibility="visible")

# 5) Explanation (taller but compact)
exp = st.text_area(" ", value=ss.get(f"exp_in_{rk}", _txt(ta_exp)),
                   key=f"exp_in_{rk}", label_visibility="collapsed",
                   placeholder="விளக்கம் / Explanation", height=160)

# Merge back to QC_TA
def _save_current():
    merged = build_ta_text(q, a, b, c, d, st.session_state[f"ans_in_{rk}"], exp)
    ss.qc_work.at[ss.qc_idx, "QC_TA"] = merged

# 6) Buttons directly under explanation (no space below)
bL, bC, bR = st.columns([1,1,1])
with bL:
    if st.button("💾 Save", use_container_width=True):
        _save_current()
with bC:
    if st.button("✅ Mark Complete", use_container_width=True):
        _save_current()
with bR:
    if st.button("📄 Save & Next", use_container_width=True, disabled=ss.qc_idx>=total-1):
        _save_current()
        ss.qc_idx += 1
        st.rerun()
