# pages/03_Email_QC_Panel.py
# SME-only compact editor: two buttons bottom, options tighter, answer on its own row
import io, re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")

# ------------------- CSS: compact page & inputs -------------------
st.markdown("""
<style>
/* Hide sidebar + top chrome for SME view */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"] {visibility:hidden;height:0;}
/* Smaller paddings; tiny bottom so no empty space */
main .block-container {padding-top:12px; padding-bottom:12px;}
/* Panel looks */
.box{border:1px solid #d9d9d9;border-radius:12px;padding:10px 12px;margin:8px 0}
.box.en{background:#eaf2ff;border-color:#9cc4ff}
.box.ta{background:#eaf7ec;border-color:#8ed39a}
.label{display:inline-block;background:#eef1f3;padding:2px 8px;border-radius:6px;font-size:.9rem;margin-bottom:6px}
/* Inputs compact */
div[data-testid="stTextInput"]>div>label,
div[data-testid="stTextArea"]>div>label {display:none !important;}
div[data-testid="stTextInput"], div[data-testid="stTextArea"] {margin-bottom:6px;}
input, textarea {font-size:16px;}
/* Option grid tighter */
.optrow {margin-top:4px; margin-bottom:0;}
/* Emphasis box for Answer row */
.answrap > div > div {border:1px solid #b5b5b5 !important; border-radius:8px !important;}
/* Button row */
.btnrow {margin-top:8px;}
</style>
""", unsafe_allow_html=True)

# ------------------- required columns -------------------
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA"
]

# ------------------- helpers -------------------
def _txt(v):
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return ["","","",""]
    parts = re.split(r"\s*(?:\\r\\n|\\n|[|•;])\s*", t)
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
    # csv first
    try:
        return pd.read_csv(url)
    except Exception:
        pass
    # then xlsx
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
    out = pd.DataFrame()
    for k in col_map:
        src = col_map[k]
        if src is None:
            if k=="QC_TA":
                out[k] = ""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k] = df[src]
    return out.reset_index(drop=True)

def apply_subset(df: pd.DataFrame) -> pd.DataFrame:
    # allow deep-link ?ids=1,2 or ?rows=11-25
    try:
        qp = st.query_params
    except Exception:
        qp = st.experimental_get_query_params()
    ids = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        id_list = re.split(r"[,\s]+", ids[0].strip())
        id_list = [x for x in id_list if x!=""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b = int(m.group(1)), int(m.group(2))
            a=max(1,a); b=max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ------------------- session -------------------
ss=st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),("link_in",""),("dl_buf",None)]:
    if k not in ss: ss[k]=v

# ------------------- deep-link auto load -------------------
try:
    qp = st.query_params
except Exception:
    qp = st.experimental_get_query_params()
auto_file = qp.get("file", [])
if auto_file and ss.qc_work.empty:
    try:
        df = read_from_link(auto_file[0])
        df = normalize_columns(df)
        df = apply_subset(df)
        if "QC_TA" not in df.columns: df["QC_TA"]=""
        ss.qc_src = df.copy(); ss.qc_work = df.copy(); ss.qc_idx=0
    except Exception as e:
        st.error(str(e))

# ------------------- Admin loader (only when empty) -------------------
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
                    if upl.name.lower().endswith(".csv"): df=pd.read_csv(upl)
                    else: df=pd.read_excel(upl)
                else:
                    if not ss.link_in.strip(): raise RuntimeError("Upload a file or paste a link, then Load.")
                    df=read_from_link(ss.link_in)
                df = normalize_columns(df)
                df = apply_subset(df)
                if "QC_TA" not in df.columns: df["QC_TA"]=""
                ss.qc_src = df.copy(); ss.qc_work = df.copy(); ss.qc_idx=0
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))
    st.stop()

# ------------------- Top status -------------------
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

# ------------------- Reference panels -------------------
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br>"
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

# ------------------- SME Edit Console -------------------
st.subheader("SME Edit Console / ஆசிரியர் திருத்தம்")

A,B,C,D = _split_opts(ta_op)
rk=f"r{ss.qc_idx}"
for k,v in [
    (f"q_{rk}",_txt(ta_q)), (f"a_{rk}",A),(f"b_{rk}",B),(f"c_{rk}",C),(f"d_{rk}",D),
    (f"ans_{rk}",_txt(ta_ans)), (f"exp_{rk}",_txt(ta_exp))
]:
    if k not in ss: ss[k]=v

# Question (≈2 lines)
q = st.text_area(" ", value=ss[f"q_{rk}"], key=f"q_in_{rk}", height=72,
                 label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")

# Row 1: A | B (tight)
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
r1c1, r1c2 = st.columns(2)
with r1c1:
    a = st.text_input(" ", value=ss[f"a_{rk}"], key=f"a_in_{rk}",
                      label_visibility="collapsed", placeholder="A")
with r1c2:
    b = st.text_input("  ", value=ss[f"b_{rk}"], key=f"b_in_{rk}",
                      label_visibility="collapsed", placeholder="B")
st.markdown("</div>", unsafe_allow_html=True)

# Row 2: C | D (tight)
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
r2c1, r2c2 = st.columns(2)
with r2c1:
    c = st.text_input("   ", value=ss[f"c_{rk}"], key=f"c_in_{rk}",
                      label_visibility="collapsed", placeholder="C")
with r2c2:
    d = st.text_input("    ", value=ss[f"d_{rk}"], key=f"d_in_{rk}",
                      label_visibility="collapsed", placeholder="D")
st.markdown("</div>", unsafe_allow_html=True)

# Row 3: Answer (own row, centered width)
ac1, ac2, ac3 = st.columns([1,2,1])
with ac2:
    st.markdown("<div class='answrap'>", unsafe_allow_html=True)
    ans = st.text_input("     ", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}",
                        label_visibility="collapsed", placeholder="பதில் / Answer")
    st.markdown("</div>", unsafe_allow_html=True)

# Explanation (taller)
exp = st.text_area("      ", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}", height=200,
                   label_visibility="collapsed", placeholder="விளக்கம் / Explanation")

def _save_current():
    merged = build_ta_text(q,a,b,c,d,ans,exp)
    ss.qc_work.at[ss.qc_idx,"QC_TA"]=merged

# ------------------- Bottom buttons: ONLY two -------------------
bL, spacer, bR = st.columns([1,1,1])
with bL:
    if st.button("✅ வேலை முடிந்தது — QC கோப்பு சேமிக்க", use_container_width=True):
        _save_current()
        buf = io.BytesIO()
        ss.qc_work.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ QC Excel (.xlsx)", data=buf,
                           file_name="qc_verified.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
with bR:
    if st.button("▶ சேமித்து அடுத்தது / Save & Next", use_container_width=True,
                 disabled=ss.qc_idx>=len(ss.qc_work)-1):
        _save_current()
        ss.qc_idx += 1
        st.experimental_rerun()
