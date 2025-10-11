# pages/03_Email_QC_Panel.py
# SME compact editor: 6 rows, centered title, minimal gaps,
# Go button on the LEFT of Vocabulary, Answer on RIGHT, ~45vh height.

import io, re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= CSS (compact & layout control) =================
st.markdown("""
<style>
/* Hide sidebar & top chrome for SME view */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"] {visibility:hidden;height:0;}
/* Compact paddings + remove bottom empties */
main .block-container {padding-top:10px; padding-bottom:0;}
section[data-testid="stSidebarContent"]{padding-top:0 !important}

/* Cards for reference panels */
.box{border:1px solid #d9d9d9;border-radius:12px;padding:10px 12px;margin:8px 0}
.box.en{background:#eaf2ff;border-color:#9cc4ff}
.box.ta{background:#eaf7ec;border-color:#8ed39a}
.label{display:inline-block;background:#eef1f3;padding:2px 8px;border-radius:6px;font-size:.9rem}

/* Hide labels of inputs */
div[data-testid="stTextInput"]>div>label,
div[data-testid="stTextArea"]>div>label {display:none !important;}
/* Tighten input blocks */
div[data-testid="stTextInput"], div[data-testid="stTextArea"] {margin-bottom:4px;}
input, textarea {font-size:16px;}

/* Option rows: smallest safe gaps */
.optrow .stColumn {padding-left:4px !important; padding-right:4px !important;}
.optrow {margin-top:2px; margin-bottom:2px;}

/* Answer box slight emphasis */
.answrap > div > div {border:1px solid #5b5b5b !important; border-radius:8px !important;}

/* 3-button center bar (Row 6) */
.btrow .stColumn {padding-left:6px !important; padding-right:6px !important;}
.btrow {margin-top:6px; margin-bottom:0;}

/* Keep edit console around ~45% of viewport height */
#smeWrap {max-height:45vh;}
/* reduce extra vertical spacing made by Streamlit containers */
#smeWrap .block-container, #smeWrap [data-testid="stVerticalBlock"]{padding-bottom:0;margin-bottom:0;}
</style>
""", unsafe_allow_html=True)

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
    t=_txt(v)
    if not t: return ["","","",""]
    parts=re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts=[p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    labs=["A","B","C","D"]; vals=[a,b,c,d]
    have=[(labs[i], _txt(vals[i])) for i in range(4) if _txt(vals[i])]
    if not have: return ""
    return " | ".join([f"{L}) {V}" for L,V in have])

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
            if k=="QC_TA": out[k] = ""; continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k]=df[src]
    return out.reset_index(drop=True)

def apply_subset(df: pd.DataFrame) -> pd.DataFrame:
    qp = st.query_params
    ids = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        vals=[x for x in re.split(r"[,\\s]+", ids[0].strip()) if x]
        return df[df["ID"].astype(str).isin(vals)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\\s*(\\d+)\\s*-\\s*(\\d+)\\s*$", rows[0])
        if m:
            a,b=int(m.group(1)), int(m.group(2))
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

# Loader only if empty
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

# ================= top status (kept minimal; full header will be done next pass) =================
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

h1,h2,h3 = st.columns((2,4,2))
with h1: st.markdown("## 📝 SME QC Panel")
with h2:
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)} · ID: {rid}")
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    cprev, cnext = st.columns(2)
    with cprev:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx -= 1; st.rerun()
    with cnext:
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

# ================= SME Edit Console (SIX ROWS) =================
st.markdown(
    "<div style='text-align:center; font-weight:600; font-size:20px;'>SME Edit Console / ஆசிரியர் திருத்தம்</div>",
    unsafe_allow_html=True
)
st.markdown("<div id='smeWrap'>", unsafe_allow_html=True)

A,B,C,D = _split_opts(ta_op)
rk = f"{ss.qc_idx}"
for k,v in [
    (f"q_{rk}", _txt(ta_q)),
    (f"a_{rk}", _txt(A)), (f"b_{rk}", _txt(B)),
    (f"c_{rk}", _txt(C)), (f"d_{rk}", _txt(D)),
    (f"ans_{rk}", _txt(ta_ans)), (f"exp_{rk}", _txt(ta_exp)),
]:
    if k not in ss: ss[k]=v

# Row 1: Question (tight)
q = st.text_area(" ", value=ss[f"q_{rk}"], key=f"q_in_{rk}", height=68,
                 label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")

# Row 2: A | B (ultra-tight)
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    a = st.text_input(" ", value=ss[f"a_{rk}"], key=f"a_in_{rk}",
                      label_visibility="collapsed", placeholder="A")
with c2:
    b = st.text_input(" ", value=ss[f"b_{rk}"], key=f"b_in_{rk}",
                      label_visibility="collapsed", placeholder="B")
st.markdown("</div>", unsafe_allow_html=True)

# Row 3: C | D (ultra-tight)
st.markdown("<div class='optrow'>", unsafe_allow_html=True)
c3,c4 = st.columns(2)
with c3:
    c = st.text_input(" ", value=ss[f"c_{rk}"], key=f"c_in_{rk}",
                      label_visibility="collapsed", placeholder="C")
with c4:
    d = st.text_input(" ", value=ss[f"d_{rk}"], key=f"d_in_{rk}",
                      label_visibility="collapsed", placeholder="D")
st.markdown("</div>", unsafe_allow_html=True)

# Row 4: LEFT => Go + Vocabulary input  |  RIGHT => Answer
lc, rc = st.columns((1,1))
with lc:
    st.caption("Groceries / Vocabulary")
    # Go button on the LEFT; input to its right
    gL, gR = st.columns((1,5))
    with gL:
        if st.button("Go", key=f"vocab_go_{rk}", use_container_width=True):
            ss.vocab_query = ss.get(f"vocab_{rk}", "")
            ss.show_vocab = True
            st.rerun()
    with gR:
        ss[f"vocab_{rk}"] = st.text_input(" ", value=ss.get(f"vocab_{rk}",""),
                                          label_visibility="collapsed",
                                          placeholder="Type word")
with rc:
    st.caption("பதில் / Answer")
    st.markdown("<div class='answrap'>", unsafe_allow_html=True)
    ans = st.text_input(" ", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}",
                        label_visibility="collapsed", placeholder="Answer")
    st.markdown("</div>", unsafe_allow_html=True)

# Row 5: Explanation (taller but still compact)
exp = st.text_area(" ", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}",
                   height=168, label_visibility="collapsed",
                   placeholder="விளக்கம் / Explanation")

def _save_current():
    merged = build_ta_text(q,a,b,c,d,ans,exp)
    ss.qc_work.at[ss.qc_idx,"QC_TA"] = merged

# Row 6: Buttons centered
bL, bC, bR = st.columns((1,1,1), gap="small")
with bL:
    if st.button("💾 Save", use_container_width=True):
        _save_current(); st.toast("Saved this row")
with bC:
    if st.button("✅ Mark Complete", type="primary", use_container_width=True):
        _save_current(); st.toast("Marked complete")
with bR:
    if st.button("💾➡️ Save & Next", use_container_width=True,
                 disabled=ss.qc_idx>=len(ss.qc_work)-1):
        _save_current(); ss.qc_idx += 1; st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # end #smeWrap

# ============ Right-side Vocabulary slide (placeholder; can wire later) ============
panel_class = "show" if ss.show_vocab else ""
st.markdown(
    f"""
<div id="vocabPanel" class="{panel_class}">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <h3>📚 Vocabulary</h3>
    <a class="vocab-close" href="?">✖ Close</a>
  </div>
  <small>Query:</small>
  <div style="margin:6px 0 12px 0; padding:8px; border:1px solid #374151; border-radius:8px;">
    {st.session_state.get("vocab_query","")}
  </div>
  <div style="opacity:.85;">
    <p>Hook this to your glossary CSV/Drive when ready. Render matches here.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
# Close panel when link clicked (refresh with empty query)
if ss.show_vocab and st.query_params.get("", []):
    ss.show_vocab = False
    st.rerun()
