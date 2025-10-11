# pages/03_Email_QC_Panel.py
# SME-only single-page editor with link OR upload

import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")

# --- styles (hide chrome + sticky footer) ---
st.markdown("""
<style>
[data-testid="stSidebar"]{display:none;}
[data-testid="collapsedControl"], header, footer, .stAppToolbar {visibility:hidden;height:0;}
main .block-container {padding-bottom: 120px;}
.sme-footer{position:fixed;left:0;right:0;bottom:0;z-index:9999;background:rgba(30,30,30,.96);
  border-top:1px solid #333;padding:10px 14px}
.sme-footer .wrap{max-width:1200px;margin:0 auto}
.sme-footer label,.sme-footer p{color:#ddd!important;margin:0 0 6px 2px;font-size:.9rem}
.sme-footer .note{color:#9ad27f!important}
.box{border:1px solid #d9d9d9;border-radius:12px;padding:14px 16px;margin:10px 0}
.box.en{background:#eaf2ff;border-color:#9cc4ff}
.box.ta{background:#eaf7ec;border-color:#8ed39a}
.box.preview{background:#fffbe6;border-color:#ffe58f}
h4.title{margin:0 0 10px 0}
.label{display:inline-block;background:#eef1f3;padding:2px 8px;border-radius:6px;font-size:.9rem}
.hr{height:8px}
</style>
""", unsafe_allow_html=True)

# ---- expected columns ----
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA"
]

# ---- helpers ----
def _txt(v):
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return ["","","",""]
    import re as _re
    parts = _re.split(r"\s*(?:\\r\\n|\\n|[|•;])\s*", t)
    parts = [p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    opts=[x for x in [a,b,c,d] if _txt(x)]
    if not opts: return ""
    labels=["A","B","C","D"]
    return " | ".join(f"{labels[i]}) {opts[i]}" for i in range(len(opts)))

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q):   out.append(f"கேள்வி: {q}")
    ops=_join_opts(a,b,c,d)
    if ops:       out.append(f"விருப்பங்கள் (A–D): {ops}")
    if _txt(ans): out.append(f"பதில்: {ans}")
    if _txt(exp): out.append(f"விளக்கம்: {exp}")
    return "\n\n".join(out)

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

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_lower = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map = {
        "ID": pick("ID","Id","id"),
        "Question (English)": pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)" : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"  : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"  : pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"   : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"    : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)": pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"             : pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
    }
    miss=[k for k,v in col_map.items() if v is None]
    if miss: raise RuntimeError("Missing columns in the file: "+", ".join(miss))
    out=df[[col_map[k] for k in col_map]].copy()
    out.columns=list(col_map.keys())
    return out.reset_index(drop=True)

# ---- session defaults ----
ss=st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),
            ("link_in","")]:
    if k not in ss: ss[k]=v

# ---- sticky footer: Upload OR Link ----
st.markdown('<div class="sme-footer"><div class="wrap">', unsafe_allow_html=True)
t1,t2,t3 = st.columns([4,2,1])
with t1:
    st.write("**Upload file (CSV/XLSX)**")
    upl = st.file_uploader(" ", type=["csv","xlsx"], label_visibility="collapsed")
with t2:
    st.write("**…or paste a link**")
    ss.link_in = st.text_input(" ", value=ss.link_in, placeholder="https://…/file.csv or Google Drive link", label_visibility="collapsed")
    st.markdown('<p class="note">Tip: on iPad, long-press → Paste. Use either method.</p>', unsafe_allow_html=True)
with t3:
    if st.button("Load", use_container_width=True):
        try:
            if upl is not None:
                # read uploaded file
                if upl.name.lower().endswith(".csv"):
                    df=pd.read_csv(upl)
                else:
                    df=pd.read_excel(upl)
            else:
                if not ss.link_in.strip():
                    raise RuntimeError("Please upload a file or paste a link, then press Load.")
                df=read_from_link(ss.link_in)
            ss.qc_src = normalize_columns(df)
            ss.qc_work = ss.qc_src.copy()
            ss.qc_idx = 0
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))
st.markdown('</div></div>', unsafe_allow_html=True)

# ---- stop if nothing loaded ----
if ss.qc_work.empty:
    st.stop()

# ---- current row + header ----
row = ss.qc_work.iloc[ss.qc_idx]; rid=row["ID"]
h1,h2,h3 = st.columns([2,4,2])
with h1: st.markdown("## 📝 SME QC Panel")
with h2:
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)} · ID: {rid}")
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    p,n = st.columns(2)
    with p:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx-=1; st.experimental_rerun()
    with n:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx+=1; st.experimental_rerun()
st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

# ---- reference panels (read-only) ----
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br><br>"
        f"<b>Q:</b> {_txt(q)}<br>"
        f"<b>Options (A–D):</b> {_txt(op)}<br>"
        f"<b>Answer:</b> {_txt(ans)}<br>"
        f"<b>Explanation:</b> {_txt(exp)}"
    )
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

en_q,en_op,en_ans,en_exp = [row[c] for c in ["Question (English)","Options (English)","Answer (English)","Explanation (English)"]]
ta_q,ta_op,ta_ans,ta_exp = [row[c] for c in ["Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)"]]
view_block("English Version / ஆங்கிலம்", en_q,en_op,en_ans,en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q,ta_op,ta_ans,ta_exp, "ta")

# ---- SME Edit Console (bottom 50%) ----
st.markdown("<h4 class='title'>SME Edit Console / ஆசிரியர் திருத்தம்</h4>", unsafe_allow_html=True)
A,B,C,D = _split_opts(ta_op)
rk=f"r{ss.qc_idx}"
for k,v in [(f"q_{rk}",_txt(ta_q)),(f"a_{rk}",A),(f"b_{rk}",B),(f"c_{rk}",C),(f"d_{rk}",D),
            (f"ans_{rk}",_txt(ta_ans)),(f"exp_{rk}",_txt(ta_exp))]:
    if k not in ss: ss[k]=v

q = st.text_area("கேள்வி / Question (TA)", value=ss[f"q_{rk}"], key=f"q_in_{rk}", height=90)
c1,c2 = st.columns(2)
with c1:
    a = st.text_input("A", value=ss[f"a_{rk}"], key=f"a_in_{rk}")
    c = st.text_input("C", value=ss[f"c_{rk}"], key=f"c_in_{rk}")
with c2:
    b = st.text_input("B", value=ss[f"b_{rk}"], key=f"b_in_{rk}")
    d = st.text_input("D", value=ss[f"d_{rk}"], key=f"d_in_{rk}")
ans = st.text_input("பதில் / Answer", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}")
exp = st.text_area("விளக்கம் / Explanation", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}", height=120)

preview = build_ta_text(q,a,b,c,d,ans,exp)
st.markdown(f"<div class='box preview'><span class='label'>Live Preview / நேரடி முன்னோட்டம்</span><br><br>{preview}</div>", unsafe_allow_html=True)

b1,b2 = st.columns([1,2])
with b1:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx,"QC_TA"]=preview
        st.success("Saved.")
with b2:
    if st.button("💾 Save & Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_work.at[ss.qc_idx,"QC_TA"]=preview
        ss.qc_idx+=1
        st.experimental_rerun()
