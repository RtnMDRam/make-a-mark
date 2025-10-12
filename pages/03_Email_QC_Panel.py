# pages/03_Email_QC_Panel.py
# SME compact editor v2 — sticky 5% header, 6 rows, tight grid, top-sheet glossary

import io
import re
import pandas as pd
import streamlit as st
from datetime import datetime

# ----------------------- page config -----------------------
st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===========================================================
# Header (5% vh) — Tamil calendar label (simple month map), ID, time (24h)
# ===========================================================
TN_MONTHS = {
    1: "தை", 2: "மாசி", 3: "பங்குனி", 4: "சித்திரை", 5: "வைகாசி", 6: "ஆனி",
    7: "ஆடி", 8: "ஆவணி", 9: "புரட்டாசி", 10: "ஐப்பசி", 11: "கார்த்திகை", 12: "மார்கழி",
}
EN_MONTHS3 = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def _header_date_labels(now: datetime):
    # NOTE: This is a simple month mapping (not exact solar transit).
    ta_month = TN_MONTHS.get(now.month, "")
    en_mon = EN_MONTHS3[now.month]
    left_txt = f"{now.day} {ta_month} {now.year}  |  {en_mon} {now.day:02d}"
    right_txt = now.strftime("%H:%M")
    return left_txt, right_txt

def render_header(top_height_vh: int = 5, row_id: str = ""):
    left, right = _header_date_labels(datetime.now())
    st.markdown(
        f"""
        <style>
        .hdr {{position:sticky; top:0; z-index:9999; height:{top_height_vh}vh;
               display:flex; align-items:center; padding:0 10px;
               background:var(--background-color,#0e1117);}}
        .hdr .l {{flex:1; font-size:14px; opacity:.9}}
        .hdr .c {{flex:0 0 auto; font-weight:700; font-size:16px;
                  padding:4px 10px; border-radius:8px; background:#1e293b;}}
        .hdr .r {{flex:1; text-align:right; font-variation-settings:'wght' 600}}
        </style>
        <div class="hdr">
          <div class="l">📅 {left}</div>
          <div class="c">ID: {row_id}</div>
          <div class="r">⏱ {right}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===========================================================
# Extra CSS — compact layout + mobile friendliness
# ===========================================================
st.markdown(
    """
    <style>
    /* Hide Streamlit chrome for SME */
    [data-testid="stSidebar"]{display:none;}
    header, footer, .stAppToolbar, [data-testid="collapsedControl"]{visibility:hidden;height:0;}
    main .block-container{padding:8px 10px 6px;}
    .element-container{margin-bottom:6px;}
    hr, div[role="separator"]{display:none!important;height:0!important;margin:0!important;}

    /* Inputs smaller */
    input, textarea {font-size:16px;}
    .inpbox{border:1px solid #d9d9d9; border-radius:12px; padding:8px 12px; margin:6px 0; background:#111827;}
    .box{border:1px solid #d0d7de33; border-radius:12px; padding:10px 12px; margin:8px 0;}
    .en{background:#eaf2ff0f; border-color:#93c5fd3d;}
    .ta{background:#eaffe60f; border-color:#86efac33;}

    /* Option grid tighter */
    .oprow{margin-top:4px; margin-bottom:0;}
    .answrap > div > div {border:1px solid #525252!important; border-radius:8px!important;}

    /* SME button row */
    .btrow{margin-top:8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===========================================================
# Glossary (top-sheet) — opens from top on Go, retracts on Close/Go again
# ===========================================================
def _get_glossary_state():
    ss = st.session_state
    if "glossary" not in ss:
        # seed with a couple of examples; can be empty
        ss.glossary = [{"en":"xylem", "ta":"ஜைலம்"}, {"en":"pit", "ta":"குழி"}]
    if "show_glossary" not in ss:
        ss.show_glossary = False
    if "vocab_query" not in ss:
        ss.vocab_query = ""
    return ss

def _search_glossary(items, q):
    q = (q or "").strip()
    if not q:
        return []
    qre = re.compile(re.escape(q), re.IGNORECASE)
    return [it for it in items if qre.search(it.get("en","")) or qre.search(it.get("ta",""))]

def render_glossary_topsheet():
    ss = _get_glossary_state()
    visible = ss.show_glossary
    q = ss.vocab_query

    st.markdown(
        f"""
        <style>
        .topsheet {{
            position: fixed; left: 0; right: 0; top: 0;
            background: #0f172a; border-bottom: 1px solid #334155;
            padding: 12px 14px; z-index: 9998;
            transform: translateY({ '0' if visible else '-100%' });
            transition: transform .25s ease-in-out;
        }}
        .topsheet h4 {{margin: 0 0 6px 0;}}
        .topsheet .row {{display:flex; gap:8px; align-items:center; flex-wrap:wrap}}
        .pill {{background:#1f2937; border:1px solid #334155; border-radius:999px; padding:4px 10px; font-size:13px}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="topsheet">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        st.markdown("#### 📚 Vocabulary / களஞ்சியம்")
        st.caption("Results for: **{}**".format(q if q else "—"))
    with c2:
        if st.button("➕ Add entry", key="g_add"):
            with st.popover("Add a new glossary pair"):
                en = st.text_input("English")
                ta = st.text_input("தமிழ்")
                if st.button("Save entry", type="primary"):
                    ss.glossary.append({"en":en.strip(), "ta":ta.strip()})
                    st.rerun()
    with c3:
        if st.button("✕ Close", key="g_close", use_container_width=True):
            ss.show_glossary = False
            st.rerun()

    # results
    matches = _search_glossary(ss.glossary, q)
    if matches:
        for it in matches[:10]:
            st.markdown(f"- **{it['en']}** → {it['ta']}")
    else:
        st.info("No matches yet. Add one with **➕ Add entry**.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===========================================================
# Data loading helpers
# ===========================================================
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)"  , "Options (Tamil)"  , "Answer (Tamil)"  , "Explanation (Tamil)",
    "QC_TA"
]

def _txt(v):
    if pd.isna(v): return ""
    return str(v).replace("\r\n", "\n").strip()

def _split_opts(v):
    t = _txt(v)
    if not t: return ["","","",""]
    parts = re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts = [p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    opts = [x for x in [a,b,c,d] if _txt(x)]
    if not opts: return ""
    labels = ["A","B","C","D"]
    return " | ".join([f"{labels[i]}) {opts[i]}" for i in range(len(opts))])

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q):   out.append(f"கேள்வி: {q}")
    ops = _join_opts(a,b,c,d)
    if ops:       out.append(f"விருப்பங்கள் (A–D): {ops}")
    if _txt(ans): out.append(f"பதில்: {ans}")
    if _txt(exp): out.append(f"விளக்கம்: {exp}")
    return "\n\n".join(out)

def _clean_drive_url(url:str)->str:
    url=url.strip()
    if "drive.google.com" not in url: return url
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def read_from_link(url:str)->pd.DataFrame:
    url=_clean_drive_url(url)
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
            ln = n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map = {
        "ID": pick("ID","Id","id"),
        "Question (English)": pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)" : pick("Options (English)" ,"OPT_EN","Options_English"),
        "Answer (English)"  : pick("Answer (English)"  ,"ANS_EN","Answer_English"),
        "Explanation (English)" : pick("Explanation (English)","EXP_EN","Explanation_English"),

        "Question (Tamil)"  : pick("Question (Tamil)"  ,"Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"   : pick("Options (Tamil)"   ,"OPT_TA","Options_Tamil"),
        "Answer (Tamil)"    : pick("Answer (Tamil)"    ,"ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)": pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"             : pick("QC_TA","QC Verified (Tamil)","QC_Tamil"),
    }
    out = pd.DataFrame()
    for k, src in col_map.items():
        if src is None:
            if k == "QC_TA":
                out[k] = ""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k] = df[src]
    return out.reset_index(drop=True)

def apply_subset(df: pd.DataFrame) -> pd.DataFrame:
    # Allow deep links like ?ids=1,2 or ?rows=11-25
    try:
        qp = st.query_params
    except Exception:
        qp = {}
    ids = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        id_list = re.split(r"[, \s]+", ids[0].strip())
        id_list = [x for x in id_list if x!=""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m=re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b = int(m.group(1)), int(m.group(2))
            a=min(a,b); b=max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ===========================================================
# Session bootstrap
# ===========================================================
ss = st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0),("link_in","")]:
    if k not in ss: ss[k]=v

# Attempt deep-link auto load (?file=...)
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

# ===========================================================
# Admin loader (only if empty)
# ===========================================================
if ss.qc_work.empty:
    st.markdown("### 📝 SME QC Panel")
    st.info("Paste the CSV/XLSX link sent by Admin, or upload the file. (Shown only when data is empty.)")
    c1,c2,c3 = st.columns([4,2,1])
    with c1:
        upl = st.file_uploader("Upload file (CSV/XLSX)", type=["csv","xlsx"], label_visibility="collapsed")
    with c2:
        ss.link_in = st.text_input("…or paste link (CSV/XLSX/Drive)", value=ss.link_in, label_visibility="collapsed")
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

# ===========================================================
# Top header + row status
# ===========================================================
row = ss.qc_work.iloc[ss.qc_idx]
rid = str(row["ID"])
render_header(top_height_vh=5, row_id=rid)

h1,h2,h3 = st.columns([2,4,2])
with h1:
    st.markdown("#### 🧑‍🏫 SME QC Panel")
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)}")
with h2:
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    p,n = st.columns(2)
    with p:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx -= 1; st.rerun()
    with n:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx += 1; st.rerun()

# ===========================================================
# English & Tamil reference panels
# ===========================================================
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='pill'>{title}</span><br>"
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

# ===========================================================
# SME Edit Console — 6 rows (tight)
# ===========================================================
st.markdown("<h4 style='text-align:center'>SME Edit Console / ஆசிரியர் திருத்தம்</h4>", unsafe_allow_html=True)

# Prepare state keys for this row
A,B,C,D = _split_opts(ta_op)
rk = f"{ss.qc_idx}"
for k,v in [
    (f"q_{rk}", _txt(ta_q)), (f"a_{rk}", _txt(A)), (f"b_{rk}", _txt(B)), (f"c_{rk}", _txt(C)),
    (f"d_{rk}", _txt(D)), (f"ans_{rk}", _txt(ta_ans)), (f"exp_{rk}", _txt(ta_exp))
]:
    if k not in ss: ss[k]=v

# Render glossary top-sheet (hidden by default; toggled by Go)
render_glossary_topsheet()

# Row 1: Question (2-line height)
q = st.text_area(" ", value=ss[f"q_{rk}"], key=f"q_in_{rk}", height=72,
                 label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")

# Thin separator (visual grouping; consumes almost zero space)
st.markdown("<div style='height:4px; opacity:.35; border-bottom:1px solid #334155;'></div>", unsafe_allow_html=True)

# Row 2: A | B  (tight)
r2c1, r2c2 = st.columns(2)
with r2c1:
    a = st.text_input(" ", value=ss[f"a_{rk}"], key=f"a_in_{rk}", label_visibility="collapsed", placeholder="A")
with r2c2:
    b = st.text_input(" ", value=ss[f"b_{rk}"], key=f"b_in_{rk}", label_visibility="collapsed", placeholder="B")

# Row 3: C | D  (tight)
r3c1, r3c2 = st.columns(2)
with r3c1:
    c = st.text_input(" ", value=ss[f"c_{rk}"], key=f"c_in_{rk}", label_visibility="collapsed", placeholder="C")
with r3c2:
    d = st.text_input(" ", value=ss[f"d_{rk}"], key=f"d_in_{rk}", label_visibility="collapsed", placeholder="D")

# Row 4: Vocabulary (left) | Answer (right)
left, right = st.columns([1,1])
with left:
    st.caption("Groceries / Vocabulary")
    gocol, qcol = st.columns([1,5])
    with gocol:
        if st.button("Go", key="gloss_go", use_container_width=True):
            gss = _get_glossary_state()
            gss.show_glossary = not gss.show_glossary
            st.rerun()
    with qcol:
        gss = _get_glossary_state()
        gss.vocab_query = st.text_input("Type word", value=gss.vocab_query, label_visibility="collapsed", placeholder="Type word")
with right:
    st.caption("பதில் / Answer")
    ans_val = st.text_input(" ", value=ss[f"ans_{rk}"], key=f"ans_in_{rk}", label_visibility="collapsed", placeholder="A…")

# Row 5: Explanation (taller)
exp = st.text_area(" ", value=ss[f"exp_{rk}"], key=f"exp_in_{rk}", height=180,
                   label_visibility="collapsed", placeholder="விளக்கம் / Explanation")

# Save current row helper
def _save_current():
    merged = build_ta_text(q,a,b,c,d,ans_val,exp)
    ss.qc_work.at[ss.qc_idx,"Question (Tamil)"]      = q
    ss.qc_work.at[ss.qc_idx,"Options (Tamil)"]       = _join_opts(a,b,c,d)
    ss.qc_work.at[ss.qc_idx,"Answer (Tamil)"]        = ans_val
    ss.qc_work.at[ss.qc_idx,"Explanation (Tamil)"]   = exp
    ss.qc_work.at[ss.qc_idx,"QC_TA"]                 = merged

# Row 6: Bottom buttons (Save | Mark Complete | Save & Next)
bL, bM, bR = st.columns([1,1,1])
with bL:
    if st.button("💾 Save", use_container_width=True):
        _save_current()
        st.success("Saved.")
with bM:
    if st.button("✅ Mark Complete", use_container_width=True):
        _save_current()
        buf = io.BytesIO()
        ss.qc_work.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ QC Excel (.xlsx)", data=buf, file_name="qc_verified.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
with bR:
    if st.button("📂 Save & Next", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        _save_current()
        ss.qc_idx += 1
        st.rerun()
