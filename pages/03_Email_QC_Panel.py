# pages/03_Email_QC_Panel.py
# SME one-page compact panel (iPad 10.9"): header + loader + refs + tight editor
import io, re
import pandas as pd
import streamlit as st

# ---------- optional helpers from /lib (safe fallbacks if missing) -----------
try:
    from lib.header_bar import render_header          # date | title | time row
except Exception:
    def render_header(top_height_vh=5, title="பாட பொருள் நிபுணர் பலகை / SME Panel"):
        st.markdown(
            f"""
            <div class="hdr">
              <div class="hdr_l"><span id="dt_ta"></span><br><small>Oct 12</small></div>
              <div class="hdr_c">{title}</div>
              <div class="hdr_r" id="clock24"></div>
            </div>
            <script>
              // Tamil date (static sample – your real header_bar already does this)
              const t = new Date(); const hh = String(t.getHours()).padStart(2,'0');
              const mm = String(t.getMinutes()).padStart(2,'0');
              document.getElementById('clock24').innerText = hh+':'+mm;
              document.getElementById('dt_ta').innerText = '12 புரட்டாசி 2025';
            </script>
            """,
            unsafe_allow_html=True,
        )

try:
    from lib.admin_uploader import render_admin_loader  # compact link/upload strip
except Exception:
    def render_admin_loader():
        ss = st.session_state
        c1, c2, c3 = st.columns([6,1.6,1.2])
        with c1:
            ss._link_in = st.text_input("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.",
                                        label_visibility="collapsed")
        with c2:
            up = st.file_uploader("Upload the file here (Limit 200 MB per file)",
                                  type=["csv","xlsx"], label_visibility="collapsed")
        with c3:
            if st.button("Load", use_container_width=True):
                if up is not None:
                    df = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
                elif ss._link_in.strip():
                    url = ss._link_in.strip()
                    try:
                        df = pd.read_csv(url)
                    except Exception:
                        df = pd.read_excel(url)
                else:
                    raise RuntimeError("Give a link or upload a file.")
                df = normalize_columns(df)
                df = apply_subset(df)
                if "QC_TA" not in df.columns:
                    df["QC_TA"] = ""
                ss.qc_src = df.copy()
                ss.qc_work = df.copy()
                ss.qc_idx = 0
                st.rerun()

try:
    from lib.ux_mobile import enable_ipad_keyboard_aid, glossary_drawer
except Exception:
    def enable_ipad_keyboard_aid(): pass
    def glossary_drawer(): pass

# ---------- page config ----------
st.set_page_config(page_title="SME QC Panel", page_icon="📜", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------- theme: palm-leaf / manuscript ----------
st.markdown("""
<style>
/* Hide Streamlit chrome in SME view */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"]{visibility:hidden;height:0;}
main .block-container{padding:8px 10px 8px;}

/* Palette */
:root{
  --leaf:#F8F3E5;       /* palm leaf */
  --ink:#1c1c1c;
  --soft:#edf4ee;       /* soft green captions */
  --panel:#ffffff;
  --stroke:#c9c3b3;
  --accent:#2e7d32;
}

html, body, .stApp{background:var(--leaf);}
.card{
  background:var(--panel);
  border:1px solid var(--stroke);
  border-radius:12px;
  padding:12px 14px;
}
.hdr{
  display:grid;
  grid-template-columns:1fr 2fr 1fr;
  align-items:center;
  gap:10px;
  padding:6px 8px 0;
}
.hdr_c{
  text-align:center;
  font-weight:700;
  font-size:18px;
}
.hbar{
  margin:6px 0 4px;
  display:grid;
  grid-template-columns: 1fr 1fr 1.1fr 1fr 1.2fr 1.2fr 1.2fr;
  gap:6px;
}
.badge{background:#e9f1ff;border:1px solid #b9c9ea;border-radius:8px;padding:6px 8px;text-align:center;}
.btnrow{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;}
.btnrow .stButton>button{width:100%;padding:8px 10px;border-radius:10px;}
.btn-save{border:1px solid #8aa58a;}
.btn-next{border:1px solid #8aa5c5;}
.btn-dl{border:1px solid #a79a6c;}
.btn-mark{background:#e95757;color:white;border:0;}
.labelchip{
  display:inline-block;background:var(--soft);padding:3px 8px;border-radius:8px;
  font-size:12px;margin-bottom:6px;
}
/* Inputs tight */
input, textarea{font-size:16px;}
.optrow{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px;}
.optrow + .optrow{margin-top:6px;}
.qrow{margin-bottom:4px;}
.qa_row{display:grid;grid-template-columns: 1.1fr 1fr; gap:8px; align-items:center;}
/* Remove bottom slack */
.block-container>div:last-child{margin-bottom:0;}
</style>
""", unsafe_allow_html=True)

# ---------- utils ----------
def _txt(v):
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return ["","","",""]
    parts = re.split(r"\s*(?:\r?\n|\n|\||[•;:])\s*", t)
    parts = [p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _join_opts(a,b,c,d):
    opts=[x for x in [a,b,c,d] if _txt(x)]
    if not opts: return ""
    labels=["A","B","C","D"]
    return " | ".join([f"{labels[i]} {opts[i]}" for i in range(len(opts))])

def build_ta_text(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q): out.append(f"கேள்வி: {q}")
    ops=_join_opts(a,b,c,d)
    if ops: out.append(f"விருப்பங்கள் (A–D): {ops}")
    if _txt(ans): out.append(f"பதில்: {ans}")
    if _txt(exp): out.append(f"விளக்கம்: {exp}")
    return "\n\n".join(out)

def normalize_columns(df:pd.DataFrame)->pd.DataFrame:
    cols_lower = {c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map = {
        "ID"                 : pick("ID","Id","id"),
        "Question (English)" : pick("Question (English)","Q_EN","Question_English"),
        "Options (English)"  : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"   : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"   : pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"    : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"     : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)": pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"              : pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
    }
    out = pd.DataFrame()
    for k, src in col_map.items():
        if src is None:
            if k=="QC_TA":
                out[k]=""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k]=df[src]
    return out.reset_index(drop=True)

def apply_subset(df:pd.DataFrame)->pd.DataFrame:
    # deep-link: ?ids=1,2 or ?rows=11-25
    try:
        qp = st.query_params
    except Exception:
        qp = {}
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
            a=min(a,b); b=max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ---------- session boot ----------
ss = st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),
            ("qc_idx",0),("link_in","")]:
    if k not in ss: ss[k]=v

# ---------- header row (date/title/time) ----------
render_header()

# ---------- top action bar (Save, Mark, Save&Next, Save File + badges) ----------
def _save_current():
    row = ss.qc_work.iloc[ss.qc_idx]
    rk = f"{ss.qc_idx}"
    q  = ss.get(f"q_{rk}","")
    a  = ss.get(f"a_{rk}","")
    b  = ss.get(f"b_{rk}","")
    c  = ss.get(f"c_{rk}","")
    d  = ss.get(f"d_{rk}","")
    ans= ss.get(f"ans_{rk}","")
    exp= ss.get(f"exp_{rk}","")
    ss.qc_work.at[ss.qc_idx,"Question (Tamil)"]     = q
    ss.qc_work.at[ss.qc_idx,"Options (Tamil)"]      = _join_opts(a,b,c,d)
    ss.qc_work.at[ss.qc_idx,"Answer (Tamil)"]       = ans
    ss.qc_work.at[ss.qc_idx,"Explanation (Tamil)"]  = exp
    ss.qc_work.at[ss.qc_idx,"QC_TA"]                = build_ta_text(q,a,b,c,d,ans,exp)

def _download_bytes()->bytes:
    buf = io.BytesIO()
    ss.qc_work.to_excel(buf, index=False)
    buf.seek(0)
    return buf.getvalue()

# badges: Row #A | ID | Row #Z
if not ss.qc_work.empty:
    total = len(ss.qc_work)
    rid   = ss.qc_work.iloc[ss.qc_idx]["ID"]
else:
    total = 0; rid = "—"

c1,c2,c3,c4 = st.columns([1.1,2,1.2,1.7])
with c1:
    st.markdown(f"""
    <div class="hbar">
      <div class="badge">Row #A<br><b>{ss.qc_idx+1 if total else '—'}</b></div>
      <div class="badge">_id Number<br><b>{rid}</b></div>
      <div class="badge">Row #Z<br><b>{total}</b></div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="btnrow">""", unsafe_allow_html=True)
    b1 = st.button("💾 Save", key="btn_save", use_container_width=True)
    b2 = st.button("✅ Mark Complete", key="btn_mark", use_container_width=True)
    b3 = st.button("➡️ Save & Next", key="btn_next", use_container_width=True,
                   disabled=(ss.qc_idx >= max(total-1,0)))
    b4 = st.download_button("📥 Save File", data=_download_bytes() if total else b"",
                            file_name="qc_verified.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with c3: pass
with c4: pass

if b1 or b2 or b3:
    _save_current()
    if b3 and ss.qc_idx < total-1:
        ss.qc_idx += 1
    st.rerun()

# ---------- compact loader strip (directly under the header/action bar) ----------
render_admin_loader()

# If nothing loaded yet, stop (SME just sees loader and header)
if ss.qc_work.empty:
    st.stop()

# ---------- English & Tamil reference blocks ----------
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

def _ref_block(title, q, op, ans, exp, cls):
    st.markdown(f"""
    <div class="card">
      <span class="labelchip">{title}</span>
      <div><b>Q:</b> {_txt(q)}</div>
      <div><b>Options (A–D):</b> {_txt(op)}</div>
      <div><b>Answer:</b> {_txt(ans)}</div>
      <div><b>Explanation:</b> {_txt(exp)}</div>
    </div>
    """, unsafe_allow_html=True)

_ref_block("English Version / ஆங்கிலம்",
           row["Question (English)"], row["Options (English)"],
           row["Answer (English)"], row["Explanation (English)"], "en")

_ref_block("Tamil Original / தமிழ் மூலப் பதிப்பு",
           row["Question (Tamil)"], row["Options (Tamil)"],
           row["Answer (Tamil)"], row["Explanation (Tamil)"], "ta")

# ---------- SME EDITOR (tight grid = 6 rows) ----------
st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

rk = f"{ss.qc_idx}"
# prime state defaults once per row
for k,v in [
    (f"q_{rk}",  _txt(row["Question (Tamil)"])),
    (f"a_{rk}",  _split_opts(row["Options (Tamil)"])[0]),
    (f"b_{rk}",  _split_opts(row["Options (Tamil)"])[1]),
    (f"c_{rk}",  _split_opts(row["Options (Tamil)"])[2]),
    (f"d_{rk}",  _split_opts(row["Options (Tamil)"])[3]),
    (f"ans_{rk}",_txt(row["Answer (Tamil)"])),
    (f"exp_{rk}",_txt(row["Explanation (Tamil)"])),
]:
    if k not in ss: ss[k]=v

# Question (≈2 lines)
st.text_area(" ", key=f"q_{rk}", value=ss[f"q_{rk}"], height=70, label_visibility="collapsed")

# thin separator
st.markdown('<hr style="margin:4px 0 8px 0;height:1px;border:0;background:#e0e0e0;">',
            unsafe_allow_html=True)

# Options grid 2x2
oa, ob = st.columns(2)
with oa:
    st.text_input(" ", key=f"a_{rk}", value=ss[f"a_{rk}"], label_visibility="collapsed",
                  placeholder="A) …")
with ob:
    st.text_input(" ", key=f"b_{rk}", value=ss[f"b_{rk}"], label_visibility="collapsed",
                  placeholder="B) …")
oc, od = st.columns(2)
with oc:
    st.text_input(" ", key=f"c_{rk}", value=ss[f"c_{rk}"], label_visibility="collapsed",
                  placeholder="C) …")
with od:
    st.text_input(" ", key=f"d_{rk}", value=ss[f"d_{rk}"], label_visibility="collapsed",
                  placeholder="D) …")

# Glossary + Answer row
gcol, acol = st.columns([1.05,1])
with gcol:
    st.caption("சொல் அகராதி / Glossary")
    glossary_drawer()     # your top pop-over / drawer (no panel at bottom)
    st.text_input("(Type the word)", key=f"gl_{rk}", label_visibility="collapsed")
with acol:
    st.caption("பதில் / Answer")
    st.text_input(" ", key=f"ans_{rk}", value=ss[f"ans_{rk}"], label_visibility="collapsed",
                  placeholder="A: …")

# Explanation (taller)
st.caption("விளக்கம் :")
st.text_area(" ", key=f"exp_{rk}", value=ss[f"exp_{rk}"], height=150,
             label_visibility="collapsed")

# nothing at the bottom — buttons live in the header bar
enable_ipad_keyboard_aid()
