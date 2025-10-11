# pages/03_Email_QC_Panel.py
# Super-compact SME console: 6 rows, options = grid, vocab+answer inside grid,
# no bottom slack, no experimental_rerun.

import io, re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")

# ----------------- CSS: ruthless compaction -----------------
st.markdown("""
<style>
/* Hide sidebar + chrome */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"]{visibility:hidden;height:0;}

/* Tighter global paddings */
main .block-container{padding:8px 10px 6px;}
/* Remove default element bottom gaps */
.block-container div[data-testid="stVerticalBlock"] > div:has(> .element-container){margin-bottom:4px;}
.element-container{margin-bottom:4px;}
/* Inputs compact */
div[data-testid="stTextInput"]>div>label,
div[data-testid="stTextArea"]>div>label{display:none !important;}
input, textarea{font-size:16px;}
/* Question/Explanation heights */
.qbox textarea{height:60px !important;}
.expbox textarea{height:132px !important;}

/* Options grid wrapper */
.gridwrap{border:1px solid #c9c9c9;border-radius:10px;padding:6px 8px;margin:4px 0;}
.optrow{margin:0}
.optrow .stColumn{padding-left:4px !important;padding-right:4px !important;}
.optrow input{height:34px !important;}

/* Vocab+Answer row inside grid */
.vrow .stColumn{padding-left:4px !important;padding-right:4px !important;}
.vrow input{height:34px !important;}
.vbtn button{padding:4px 10px; height:34px;}

/* Buttons row (no extra bottom) */
.btrow .stColumn{padding-left:6px !important;padding-right:6px !important;}
.btrow button{padding:8px 10px;}
/* Remove trailing space under last block */
section.main > div.block-container > div:last-child{margin-bottom:0 !important; padding-bottom:0 !important;}

/* Reference panels (kept) */
.box{border:1px solid #d9d9d9;border-radius:12px;padding:10px 12px;margin:6px 0}
.box.en{background:#eaf2ff;border-color:#9cc4ff}
.box.ta{background:#eaf7ec;border-color:#8ed39a}
.label{display:inline-block;background:#eef1f3;padding:2px 8px;border-radius:6px;font-size:.9rem}

/* Keep edit console to ≈45% viewport so English/Tamil fit above */
#smeWrap{max-height:45vh;}
</style>
""", unsafe_allow_html=True)

# ----------------- required cols -----------------
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA",
]

# ----------------- helpers -----------------
def _txt(v): 
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return ["","","",""]
    parts=re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts=[p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    labs=["A","B","C","D"]; vals=[a,b,c,d]
    have=[(labs[i], _txt(vals[i])) for i in range(4) if _txt(vals[i])]
    return " | ".join([f"{L}) {V}" for L,V in have]) if have else ""

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q):   out.append(f"கேள்வி: {q}")
    ops=_join_opts(a,b,c,d)
    if ops:       out.append(f"விருப்பங்கள் (A–D): {ops}")
    if _txt(ans): out.append(f"பதில்: {ans}")
    if _txt(exp): out.append(f"விளக்கம்: {exp}")
    return "\n\n".join(out)

def _clean_drive(url:str)->str:
    url=url.strip()
    if "drive.google.com" not in url: return url
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def read_from_link(url:str)->pd.DataFrame:
    url=_clean_drive(url)
    try: return pd.read_csv(url)
    except Exception: pass
    try: return pd.read_excel(url)
    except Exception as e: raise RuntimeError(f"Could not open link. Expecting CSV/XLSX. Details: {e}")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_lower={c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    cmap={
        "ID"                   : pick("ID","Id","id"),
        "Question (English)"   : pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)"    : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"     : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"     : pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"      : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"       : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)"  : pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"                : pick("QC_TA","QC Verified (Tamil)","QC_Tamil"),
    }
    out=pd.DataFrame()
    for k,src in cmap.items():
        if src is None:
            if k=="QC_TA": out[k]=""; continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k]=df[src]
    return out.reset_index(drop=True)

def apply_subset(df: pd.DataFrame) -> pd.DataFrame:
    qp = st.query_params
    ids = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        vals=[x for x in re.split(r"[,\s]+", ids[0].strip()) if x]
        return df[df["ID"].astype(str).isin(vals)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b=int(m.group(1)),int(m.group(2))
            if a>b: a,b=b,a
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ----------------- session -----------------
ss=st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),("link_in","")]:
    if k not in ss: ss[k]=v

# Deep-link autoload
auto_file = st.query_params.get("file", [])
if auto_file and ss.qc_work.empty:
    try:
        df = read_from_link(auto_file[0])
        df = normalize_columns(df)
        df = apply_subset(df)
        if "QC_TA" not in df.columns: df["QC_TA"]=""
        ss.qc_src=df.copy(); ss.qc_work=df.copy(); ss.qc_idx=0
        st.rerun()
    except Exception as e:
        st.error(str(e))

# Loader (only if empty)
if ss.qc_work.empty:
    st.markdown("### 📝 SME QC Panel")
    st.info("Paste the CSV/XLSX link sent by Admin, or upload the file.")
    c1,c2,c3 = st.columns((4,2,1))
    with c1: upl = st.file_uploader("Upload file (CSV/XLSX)", type=["csv","xlsx"])
    with c2: ss.link_in = st.text_input("…or paste link (CSV/XLSX/Drive)", value=ss.link_in)
    with c3:
        if st.button("Load", use_container_width=True):
            try:
                if upl is not None:
                    df = pd.read_csv(upl) if upl.name.lower().endswith(".csv") else pd.read_excel(upl)
                else:
                    if not ss.link_in.strip(): raise RuntimeError("Upload a file or paste a link.")
                    df = read_from_link(ss.link_in)
                df = normalize_columns(df)
                df = apply_subset(df)
                if "QC_TA" not in df.columns: df["QC_TA"]=""
                ss.qc_src=df.copy(); ss.qc_work=df.copy(); ss.qc_idx=0
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.stop()

# ----------------- top (minimal) -----------------
row = ss.qc_work.iloc[ss.qc_idx]; rid=row["ID"]
h1,h2,h3 = st.columns((2,4,2))
with h1: st.markdown("## 📝 SME QC Panel")
with h2:
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)} · ID: {rid}")
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    p,n = st.columns(2)
    with p:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx-=1; st.rerun()
    with n:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx+=1; st.rerun()

# ----------------- reference panels (kept) -----------------
def view_block(title, q, op, ans, exp, cls):
    html = (f"<span class='label'>{title}</span><br>"
            f"<b>Q:</b> {_txt(q)}<br>"
            f"<b>Options (A–D):</b> {_txt(op)}<br>"
            f"<b>Answer:</b> {_txt(ans)}<br>"
            f"<b>Explanation:</b> {_txt(exp)}")
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

en_q,en_op,en_ans,en_exp = [row[c] for c in ("Question (English)","Options (English)","Answer (English)","Explanation (English)")]
ta_q,ta_op,ta_ans,ta_exp = [row[c] for c in ("Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)")]

view_block("English Version / ஆங்கிலம்", en_q,en_op,en_ans,en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q,ta_op,ta_ans,ta_exp, "ta")

# ----------------- SME Edit Console (exactly 6 rows) -----------------
st.markdown(
    "<div style='text-align:center;font-weight:600;font-size:20px;'>SME Edit Console / ஆசிரியர் திருத்தம்</div>",
    unsafe_allow_html=True
)
st.markdown("<div id='smeWrap'>", unsafe_allow_html=True)

A,B,C,D = _split_opts(ta_op)
rk=str(ss.qc_idx)
for k,v in [(f"q_{rk}",_txt(ta_q)),(f"a_{rk}",_txt(A)),(f"b_{rk}",_txt(B)),(f"c_{rk}",_txt(C)),(f"d_{rk}",_txt(D)),(f"ans_{rk}",_txt(ta_ans)),(f"exp_{rk}",_txt(ta_exp))]:
    if k not in ss: ss[k]=v

# Row 1: Q
st.markdown("<div class='qbox'>", unsafe_allow_html=True)
q = st.text_area(" ", value=ss[f"q_{rk}"], key=f"q_in_{rk}", label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")
st.markdown("</div>", unsafe_allow_html=True)

# Row 2-3-4 inside a SINGLE grid wrapper to kill gaps:
st.markdown("<div class='gridwrap'>", unsafe_allow_html=True)

# Row 2: A | B
r2c1, r2c2 = st.columns(2)
with r2c1:
    a = st.text_input(" ", value=ss[f"a_{rk}"], key=f"a_in_{rk}", label_visibility="collapsed", placeholder="A")
with r2c2:
    b = st.text_input(" ", value=ss[f"b_{rk}"], key=f"b_in_{rk}", label_visibility="collapsed", placeholder="B")

# Row 3: C | D
r3c1, r3c2 = st.columns(2)
with r3c1:
    c = st.text_input(" ", value=ss[f"c_{rk}"], key=f"c_in_{rk}", label_visibility="collapsed", placeholder="C")
with r3c2:
    d = st.text_input(" ", value=ss[f"d_{rk}"], key=f"d_in_{rk}", label_visibility="collapsed", placeholder="D")

# Row 4 (inside same wrapper): Vocabulary+Go | Answer
vL, vR = st.columns(2)
with vL:
    st.caption("Groceries / Vocabulary")
    g1,g2 = st.columns((1,5))
    with g1:
        st.button("Go", key=f"v_go_{rk}", use_container_width=True, help="(stub)", type="secondary")
    with g2:
        st.text_input(" ", key=f"vocab_{rk}", value="", label_visibility="collapsed", placeholder="Type word")
with vR:
    st.caption("பதில் / Answer")
    ans = st.text_input(" ", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}", label_visibility="collapsed", placeholder="Answer")

st.markdown("</div>", unsafe_allow_html=True)  # end gridwrap

# Row 5: Explanation
st.markdown("<div class='expbox'>", unsafe_allow_html=True)
exp = st.text_area(" ", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}", label_visibility="collapsed", placeholder="விளக்கம் / Explanation")
st.markdown("</div>", unsafe_allow_html=True)

def _save_current():
    merged = build_ta_text(q,a,b,c,d,ans,exp)
    ss.qc_work.at[ss.qc_idx,"QC_TA"]=merged

# Row 6: Buttons (no extra bottom)
bL,bC,bR = st.columns((1,1,1), gap="small")
with bL:
    if st.button("💾 Save", use_container_width=True):
        _save_current(); st.toast("Saved this row")
with bC:
    if st.button("✅ Mark Complete", type="primary", use_container_width=True):
        _save_current(); st.toast("Marked complete")
with bR:
    if st.button("💾➡️ Save & Next", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        _save_current(); ss.qc_idx+=1; st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # end smeWrap
