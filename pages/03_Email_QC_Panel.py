# pages/03_Email_QC_Panel.py
# SME compact editor (traditional theme, tight grid)

import io, re, datetime as dt
import pandas as pd
import streamlit as st

# ============ Page config ============
st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============ Traditional palette + CSS compaction ============
st.markdown("""
<style>
/* hide Streamlit chrome for clean, app-like look */
[data-testid="stSidebar"]{display:none;}
header, footer, [data-testid="collapsedControl"]{visibility:hidden;height:0;}
/* global rhythm */
main .block-container{padding:8px 10px 6px;}
.element-container{margin-bottom:6px;}
hr, div[role="separator"]{display:none !important;height:0 !important;margin:0 !important;}
/* typography tuned for Tamil + English */
html, body, [data-testid="stMarkdownContainer"]{
  font-size:16.5px; line-height:1.35;
  font-variation-settings:"wght" 460;
}
/* palette: ink/stone/indigo accents */
:root{
 --ink:#0f172a;          /* slate-900 */
 --stone:#f5f5f4;        /* stone-100 */
 --stone-200:#e7e5e4;
 --stone-300:#d6d3d1;
 --indigo:#3730a3;       /* indigo-700 */
 --indigo-soft:#eef2ff;  /* indigo-50 */
 --green:#15803d;        /* success */
 --amber:#b45309;        /* accent */
}
/* HEADER BAR */
.topbar{background:var(--ink); color:white; padding:8px 12px; border-radius:8px;}
.toprow{display:grid; grid-template-columns: 120px 1fr 120px; align-items:center;}
.topdate, .toptime{opacity:.95; font-weight:600; text-align:center;}
.topdate{border-right:1px solid rgba(255,255,255,.12);}
.toptime{border-left:1px solid rgba(255,255,255,.12);}
.topttl{font-weight:700; text-align:center;}
.badge{display:inline-block; padding:4px 10px; border-radius:999px; background:rgba(255,255,255,.08); margin-left:8px;}
/* ADMIN LOADER STRIP */
.loader{background:var(--stone); border:1px solid var(--stone-300); border-radius:8px; padding:8px;}
.loader .row{display:grid; grid-template-columns: 1fr 110px; gap:8px;}
.loader input{height:36px;}
/* reference panels */
.box{border:1px solid var(--stone-300); border-radius:10px; padding:12px; background:#fafafa;}
.box.en{background:#eef2ff;border-color:#c7d2fe;}
.box.ta{background:#f0fdf4;border-color:#bbf7d0;}
.label{display:inline-block; background:var(--stone-200); border-radius:8px; padding:3px 8px; font-size:.9rem; color:#374151; margin-bottom:6px;}
/* SME grid */
.sme-title{text-align:center; font-weight:800; color:var(--indigo);}
.input-lite .stTextInput>div>div>input,
.input-lite .stTextArea>div>div>textarea{
  font-size:16px; background:white !important; border:1px solid var(--stone-300);
}
.optgrid{display:grid; grid-template-columns:1fr 1fr; gap:8px;}
.rowbar{height:4px; background:var(--stone-300); border-radius:999px; margin:6px 0 8px;}
/* answer row emphasis */
.answrap > div > div{border:1px solid #a8a29e !important; border-radius:8px !important;}
/* bottom buttons */
.btnrow{display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:8px;}
.btnrow .stButton>button{width:100%; height:40px; border-radius:10px; font-weight:700;}
.btn-save .stButton>button{background:#f8fafc; border:1px solid var(--stone-300); color:#111827;}
.btn-next .stButton>button{background:#f8fafc; border:1px solid var(--stone-300); color:#111827;}
.btn-mark .stButton>button{background:#16a34a; color:white; border:none;}
/* tighten labels */
.stTextInput>label, .stTextArea>label{display:none;}
/* avoid bottom slack */
.block-container > div:last-child{margin-bottom:0;}
</style>
""", unsafe_allow_html=True)

# ============ Utilities ============
def _txt(v):
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    """Split 'A) ... | B) ...' OR newline/semicolon/pipe separated; always return 4"""
    t=_txt(v)
    if not t: return ["","","",""]
    parts=re.split(r"\s*(?:\r?\n|\n|\||[;︱])\s*", t)
    parts=[p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    labels=["A","B","C","D"]; opts=[a,b,c,d]
    opts=[o for o in opts if _txt(o)]
    if not opts: return ""
    return " | ".join(f"{labels[i]}) {opts[i]}" for i in range(len(opts)))

def _build_ta(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q): out.append(f"Q: {q}")
    ops=_join_opts(a,b,c,d)
    if ops: out.append(f"Options (A–D): {ops}")
    if _txt(ans): out.append(f"Answer: {ans}")
    if _txt(exp): out.append(f"Explanation: {exp}")
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
    except Exception:
        pass
    try:
        return pd.read_excel(url)
    except Exception as e:
        raise RuntimeError(f"Could not open link. Expecting CSV/XLSX. Details: {e}")

def normalize_columns(df:pd.DataFrame)->pd.DataFrame:
    cols_lower={c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map={
        "ID"                   : pick("ID","Id","id"),
        "Question (English)"   : pick("Question (English)","Q_EN","Question_English"),
        "Options (English)"    : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"     : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"     : pick("Question (Tamil)","Q_TA","Question_Tamil"),
        "Options (Tamil)"      : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"       : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)"  : pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"                : pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
    }
    out=pd.DataFrame()
    for k, src in col_map.items():
        if src is None:
            if k=="QC_TA":
                out[k]=""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k]=df[src]
    return out.reset_index(drop=True)

def apply_subset(df:pd.DataFrame)->pd.DataFrame:
    # honor ?ids=… or ?rows=…
    qp=st.query_params
    ids=qp.get("ids", [])
    rows=qp.get("rows", [])
    if ids:
        id_list=re.split(r"[\s,]+", ids[0].strip())
        id_list=[x for x in id_list if x!=""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b=int(m.group(1)), int(m.group(2))
            a=min(a,b); b=max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ============ Session boot ============
ss=st.session_state
for k,v in (("qc_src",pd.DataFrame()),
            ("qc_work",pd.DataFrame()),
            ("qc_idx",0),
            ("link_in","")):
    if k not in ss: ss[k]=v

# ============ Header (Date / Title / Time) ============
def tamil_date(d:dt.date)->str:
    # simple format "26 புரட்டாசி 2025 Oct 12"
    months_ta=["தை","மாசி","பங்குனி","சித்திரை","வைகாசி","ஆனி","ஆடி","ஆவணி","புரட்டாசி","ஐப்பசி","கார்த்திகை","மார்கழி"]
    # not a true Tamil calendar conversion; using name only for month mapping
    return f"{d.day} {months_ta[(d.month-1)%12]} {d.year} Oct {d.strftime('%d')}" if d.month==10 else f"{d.day} {months_ta[(d.month-1)%12]} {d.year}"

with st.container():
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,4,1])
    with c1: st.markdown(f'<div class="toprow"><div class="topdate">{tamil_date(dt.date.today())}</div></div>', unsafe_allow_html=True)
    with c2:
        rid=f'{ss.qc_work.at[ss.qc_idx,"ID"]}' if not ss.qc_work.empty else "—"
        st.markdown(f'<div class="toprow"><div class="topttl">பாட பொருள் நிபுணர் பலகை <span class="badge">ID: {rid}</span></div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="toprow"><div class="toptime">{dt.datetime.now().strftime("%H:%M")}</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ============ Admin loader strip (always just under header) ============
def render_admin_loader():
    with st.container():
        st.markdown('<div class="loader">', unsafe_allow_html=True)
        st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")
        r1c1, r1c2 = st.columns([1,0.20])
        with r1c1:
            ss.link_in = st.text_input("", value=ss.link_in, placeholder="Paste the CSV/XLSX link", label_visibility="collapsed")
        with r1c2:
            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
            go = st.button("Load", use_container_width=True)
        r2u = st.file_uploader("Upload the file here (Limit 200 MB per file)", type=["csv","xlsx"], label_visibility="visible")
        st.markdown("</div>", unsafe_allow_html=True)

        if go:
            try:
                if ss.link_in.strip():
                    df=read_from_link(ss.link_in)
                elif r2u is not None:
                    if r2u.name.lower().endswith(".csv"):
                        df=pd.read_csv(r2u)
                    else:
                        df=pd.read_excel(r2u)
                else:
                    raise RuntimeError("Provide a link or upload a file.")
                df=normalize_columns(df)
                df=apply_subset(df)
                if "QC_TA" not in df.columns: df["QC_TA"]=""
                ss.qc_src=df.copy(); ss.qc_work=df.copy(); ss.qc_idx=0
                st.success(f"Loaded {len(df)} rows.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

# Show loader only when nothing loaded yet (SMEs see it at top before data)
if ss.qc_work.empty:
    render_admin_loader()

# Stop early if still empty
if ss.qc_work.empty:
    st.stop()

# ============ Navigation / status line ============
row=ss.qc_work.iloc[ss.qc_idx]
rid=row["ID"]
st.caption(f"English ⇄ Tamil • Row {ss.qc_idx+1}/{len(ss.qc_work)} • ID: {rid}")
st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))

# ============ Reference panels ============

def view_block(title, q, op, ans, exp, cls):
    html = (
        f'<span class="label">{title}</span>'
        f'<div><b>Q:</b> {_txt(q)}</div>'
        f'<div><b>Options (A–D):</b> {_txt(op)}</div>'
        f'<div><b>Answer:</b> {_txt(ans)}</div>'
        f'<div><b>Explanation:</b> {_txt(exp)}</div>'
    )
    st.markdown(f'<div class="box {cls}">{html}</div>', unsafe_allow_html=True)

en_q,en_op,en_ans,en_exp = [row[c] for c in ("Question (English)","Options (English)","Answer (English)","Explanation (English)")]
ta_q,ta_op,ta_ans,ta_exp = [row[c] for c in ("Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)")]

view_block("English Version / ஆங்கிலம்", en_q,en_op,en_ans,en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q,ta_op,ta_ans,ta_exp, "ta")

st.markdown('<div class="rowbar"></div>', unsafe_allow_html=True)

# ============ SME Edit Console (6-row grid) ============
st.markdown('<div class="sme-title">SME Edit Console / ஆசிரியர் திருத்தம்</div>', unsafe_allow_html=True)

rk=f"r{ss.qc_idx}"

# 1) Question (tight)
st.markdown("", help=None)
q_in = st.text_area(" ", value=_txt(ta_q), height=64, label_visibility="collapsed")

# 2) Options A/B | C/D grid (tight)
A,B,C,D=_split_opts(ta_op)
st.markdown('<div class="optgrid input-lite">', unsafe_allow_html=True)
a_in = st.text_input(" ", value=A,  placeholder="A) …", label_visibility="collapsed")
b_in = st.text_input(" ", value=B,  placeholder="B) …", label_visibility="collapsed")
c_in = st.text_input(" ", value=C,  placeholder="C) …", label_visibility="collapsed")
d_in = st.text_input(" ", value=D,  placeholder="D) …", label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

# 3) Glossary (left) + Answer (right)
gL, gR = st.columns([1,1])
with gL:
    st.markdown("**சொல் அகராதி / Glossary**")
    st.text_input(" ", placeholder="(Type the word)", label_visibility="collapsed", key=f"gloss_{rk}")
with gR:
    st.markdown("**பதில் / Answer**")
    ans_in = st.text_input(" ", value=_txt(ta_ans), placeholder="(Auto from options)", label_visibility="collapsed")

# 4) Explanation (taller)
st.markdown("**விளக்கங்கள் :**")
exp_in = st.text_area(" ", value=_txt(ta_exp), height=120, label_visibility="collapsed")

# ============ Save helpers ============
def save_current(mark_complete=False, goto_next=False):
    ss.qc_work.at[ss.qc_idx,"Question (Tamil)"]=q_in
    ss.qc_work.at[ss.qc_idx,"Options (Tamil)"]=_join_opts(a_in,b_in,c_in,d_in)
    ss.qc_work.at[ss.qc_idx,"Answer (Tamil)"]=ans_in
    ss.qc_work.at[ss.qc_idx,"Explanation (Tamil)"]=exp_in
    ss.qc_work.at[ss.qc_idx,"QC_TA"]=_build_ta(q_in,a_in,b_in,c_in,d_in,ans_in,exp_in)
    if mark_complete:
        st.toast("✅ Marked complete", icon="✅")
    if goto_next and ss.qc_idx < len(ss.qc_work)-1:
        ss.qc_idx += 1
    st.rerun()

# ============ Bottom buttons (no extra slack) ============
st.markdown('<div class="btnrow">', unsafe_allow_html=True)
cL,cM,cR = st.columns(3)
with cL:
    st.markdown('<div class="btn-save">', unsafe_allow_html=True)
    if st.button("💾 Save", use_container_width=True): save_current()
    st.markdown('</div>', unsafe_allow_html=True)
with cM:
    st.markdown('<div class="btn-mark">', unsafe_allow_html=True)
    if st.button("✅ Mark Complete", use_container_width=True): save_current(mark_complete=True)
    st.markdown('</div>', unsafe_allow_html=True)
with cR:
    st.markdown('<div class="btn-next">', unsafe_allow_html=True)
    if st.button("📂 Save & Next", use_container_width=True): save_current(goto_next=True)
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
