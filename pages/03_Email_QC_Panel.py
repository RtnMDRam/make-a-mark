# pages/03_Email_QC_Panel.py
# SME compact editor with 3-button center bar, tight options, answer on right,
# and a right-side sliding Vocabulary panel triggered from left "Go" box.

import io
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= CSS (compact & slide panel) =================
st.markdown(
    """
<style>
/* Hide sidebar & top chrome for SME view */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"] {visibility:hidden;height:0;}
/* Compact paddings */
main .block-container {padding-top:12px; padding-bottom:8px;}

/* Panel cards */
.box{border:1px solid #d9d9d9;border-radius:12px;padding:10px 12px;margin:8px 0}
.box.en{background:#eaf2ff;border-color:#9cc4ff}
.box.ta{background:#eaf7ec;border-color:#8ed39a}
.label{display:inline-block;background:#eef1f3;padding:2px 8px;border-radius:6px;font-size:.9rem}

/* Inputs compact */
div[data-testid="stTextInput"]>div>label,
div[data-testid="stTextArea"]>div>label {display:none !important;}
div[data-testid="stTextInput"], div[data-testid="stTextArea"] {margin-bottom:6px;}
input, textarea {font-size:16px;}

/* Option rows: minimal gaps */
.optrow {margin-top:4px; margin-bottom:0;}
.optrow .stColumn {padding-right:6px !important; padding-left:6px !important;}
/* Answer on right: keep box edge visible */
.answrap > div > div {border:1px solid #5b5b5b !important; border-radius:8px !important;}

/* 3-button center bar */
.btrow {margin-top:8px;}
.btrow .stColumn {padding:0 6px !important;}

/* Right slide panel */
#vocabPanel {
  position: fixed; top: 0; right: -52vw; width: 50vw; height: 100vh;
  background: #111827; color:#e5e7eb; border-left: 2px solid #3b82f6;
  box-shadow: -8px 0 24px rgba(0,0,0,.25);
  z-index: 9999; transition: right .28s ease-in-out; padding:14px 16px 20px 16px;
}
#vocabPanel.show { right: 0; }
#vocabPanel h3{margin-top:6px;margin-bottom:8px}
#vocabPanel small{opacity:.8}
.vocab-close{display:inline-block;padding:6px 10px;border:1px solid #6b7280;border-radius:8px}
</style>
""",
    unsafe_allow_html=True,
)

# ================= required columns =================
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA",
]

# ================= helpers =================
def _txt(v): 
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t = _txt(v)
    if not t: return ["","","",""]
    parts = re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts = [p for p in parts if p]
    while len(parts) < 4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    labs=["A","B","C","D"]; vals=[a,b,c,d]
    have=[(labs[i], _txt(vals[i])) for i in range(4) if _txt(vals[i])]
    if not have: return ""
    return " | ".join([f"{L}) {V}" for L,V in have])

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q):  out.append(f"கேள்வி: {q}")
    ops=_join_opts(a,b,c,d)
    if ops:      out.append(f"விருப்பங்கள் (A–D): {ops}")
    if _txt(ans):out.append(f"பதில்: {ans}")
    if _txt(exp):out.append(f"விளக்கம்: {exp}")
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
        vals=[x for x in re.split(r"[, \s]+", ids[0].strip()) if x]
        return df[df["ID"].astype(str).isin(vals)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b=int(m.group(1)),int(m.group(2))
            a=min(a,b); b=max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ================= session =================
ss=st.session_state
for k,v in [
    ("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),
    ("link_in",""),("show_vocab",False),("vocab_query","")
]:
    if k not in ss: ss[k]=v

# Deep-link auto file load
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

# Show loader only if empty
if ss.qc_work.empty:
    st.markdown("### 📝 SME QC Panel")
    st.info("Paste the CSV/XLSX link sent by Admin, or upload the file.")
    c1,c2,c3 = st.columns((4,2,1))
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

# ================= top status =================
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

h1,h2,h3 = st.columns((2,4,2))
with h1:
    st.markdown("## 📝 SME QC Panel")
with h2:
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)} · ID: {rid}")
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    prev_c, next_c = st.columns(2)
    with prev_c:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx -= 1; st.rerun()
    with next_c:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx += 1; st.rerun()

# ================= reference panels =================
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br>"
        f"<b>Q:</b> {_txt(q)}<br>"
        f"<b>Options (A–D):</b> {_txt(op)}<br>"
        f"<b>Answer:</b> {_txt(ans)}<br>"
        f"<b>Explanation:</b> {_txt(exp)}"
    )
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

en_q,en_op,en_ans,en_exp = [row[c] for c in (
    "Question (English)","Options (English)","Answer (English)","Explanation (English)")]
ta_q,ta_op,ta_ans,ta_exp = [row[c] for c in (
    "Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)")]

view_block("English Version / ஆங்கிலம்", en_q,en_op,en_ans,en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q,ta_op,ta_ans,ta_exp, "ta")

# ================= SME Edit Console =================
st.subheader("SME Edit Console / ஆசிரியர் திருத்தம்")

A,B,C,D = _split_opts(ta_op)
rk = f"{ss.qc_idx}"
for k,v in [
    (f"q_{rk}", _txt(ta_q)),
    (f"a_{rk}", _txt(A)),
    (f"b_{rk}", _txt(B)),
    (f"c_{rk}", _txt(C)),
    (f"d_{rk}", _txt(D)),
    (f"ans_{rk}", _txt(ta_ans)),
    (f"exp_{rk}", _txt(ta_exp)),
]:
    if k not in ss: ss[k]=v

# Question (tight)
q = st.text_area(" ", value=ss[f"q_{rk}"], key=f"q_in_{rk}", height=72,
                 label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")

# Row 1: A | B
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    a = st.text_input(" ", value=ss[f"a_{rk}"], key=f"a_in_{rk}",
                      label_visibility="collapsed", placeholder="A")
with c2:
    b = st.text_input(" ", value=ss[f"b_{rk}"], key=f"b_in_{rk}",
                      label_visibility="collapsed", placeholder="B")
st.markdown("</div>", unsafe_allow_html=True)

# Row 2: C | D
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
c3,c4 = st.columns(2)
with c3:
    c = st.text_input(" ", value=ss[f"c_{rk}"], key=f"c_in_{rk}",
                      label_visibility="collapsed", placeholder="C")
with c4:
    d = st.text_input(" ", value=ss[f"d_{rk}"], key=f"d_in_{rk}",
                      label_visibility="collapsed", placeholder="D")
st.markdown("</div>", unsafe_allow_html=True)

# Row 3: Left = Vocabulary trigger, Right = Answer
lc, rc = st.columns((1,1))
with lc:
    st.caption("Groceries / Vocabulary")
    vv = st.text_input(" ", value=ss.get("vocab_query",""), key=f"vocab_in_{rk}",
                       label_visibility="collapsed", placeholder="Type word & Go")
    lv, rv = st.columns((3,1))
    with rv:
        if st.button("Go", key=f"vocab_go_{rk}", use_container_width=True):
            ss.vocab_query = vv
            ss.show_vocab = True
            st.rerun()
with rc:
    st.caption("பதில் / Answer")
    st.markdown("<div class='answrap'>", unsafe_allow_html=True)
    ans = st.text_input(" ", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}",
                        label_visibility="collapsed", placeholder="Answer")
    st.markdown("</div>", unsafe_allow_html=True)

# Explanation (taller)
exp = st.text_area(" ", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}", height=200,
                   label_visibility="collapsed", placeholder="விளக்கம் / Explanation")

def _save_current():
    merged = build_ta_text(q,a,b,c,d,ans,exp)
    ss.qc_work.at[ss.qc_idx,"QC_TA"] = merged

# ================= Centered 3-button row =================
L, C, R = st.columns((1,1,1), gap="small")
with L:
    if st.button("💾 Save", use_container_width=True):
        _save_current()
        st.toast("Saved this row")
with C:
    if st.button("✅ Mark Complete", type="primary", use_container_width=True):
        _save_current()
        st.toast("Marked complete for this row")
with R:
    if st.button("💾➡️ Save & Next", use_container_width=True,
                 disabled=ss.qc_idx>=len(ss.qc_work)-1):
        _save_current(); ss.qc_idx += 1; st.rerun()

# ================= Right slide Vocabulary panel =================
panel_class = "show" if ss.show_vocab else ""
st.markdown(
    f"""
<div id="vocabPanel" class="{panel_class}">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <h3>📚 Vocabulary</h3>
    <form action="#" method="get">
      <button class="vocab-close" type="submit">✖ Close</button>
    </form>
  </div>
  <small>Query:</small>
  <div style="margin:6px 0 12px 0; padding:8px; border:1px solid #374151; border-radius:8px;">
    {st.session_state.get("vocab_query","")}
  </div>
  <div style="opacity:.85;">
    <p>This is a placeholder. Wire this panel to your glossary when ready:
    match the query to a CSV/Drive source and render the hits here.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Close panel when the form above is submitted (simulate with query flag)
if ss.show_vocab and st.query_params.get("", []):
    ss.show_vocab = False
    st.rerun()
