# pages/03_Email_QC_Panel.py
# SME compact editor (iPad 10.9") — palm-leaf theme, tight top bar (10%), editor ~40%

import io, re, datetime as dt
import pandas as pd
import streamlit as st

# ================= Page & Theme =================
st.set_page_config(page_title="SME QC Panel", page_icon="📜", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* Hide Streamlit chrome & “Manage app” badge */
[data-testid="stSidebar"]{display:none;}
header, footer, [data-testid="collapsedControl"], [data-testid="stStatusWidget"],
.viewerBadge_container__1QSob, .viewerBadge_link__1S137{display:none !important;}
/* Palm-leaf background + typographic scale */
html, body, [data-testid="stAppViewContainer"]{background:#f4ecd6;}
main .block-container{padding-top:8px; padding-bottom:4px; max-width: 880px;}
h1,h2,h3{font-weight:700;}
/* Card skins */
.box{border:1px solid #d8cfb3;border-radius:12px;padding:12px 14px; background:#fffef7;}
.box.en{background:#e9f1ff;border-color:#cfe1ff;}
.box.ta{background:#eaf6e4;border-color:#cfe9c6;}
.label{display:inline-block;background:#224; color:#fff; padding:4px 10px; border-radius:10px; font-size:.82rem;}
/* Inputs tighter */
div[data-testid="stTextInput"] > div > label,
div[data-testid="stTextArea"] > div > label {display:none !important;}
input, textarea {font-size:16px;}
hr, div[role="separator"]{display:none !important;height:0;margin:0 !important;}
/* Top bar grid */
.topbar{background:#1f2329;color:#fff;border-radius:6px;padding:6px 10px;margin:6px 0 10px;}
.topgrid{display:grid; grid-template-columns: 1fr 1fr 1fr; align-items:center; gap:8px;}
.badge{background:#343a40;color:#fff;border-radius:8px;padding:6px 10px;display:inline-block;}
.kpi{display:flex; gap:6px;}
.kpi > div{background:#e6eef8;color:#1b3a57;border-radius:8px;padding:6px 10px; min-width:76px; text-align:center;}
/* Tiny uploader strip */
.ulgrid{display:grid; grid-template-columns: 1fr 112px; gap:8px; margin:8px 0;}
/* Buttons row (now in header) */
.btns{display:flex; gap:10px; flex-wrap:wrap}
.btns .stButton>button{border-radius:10px; padding:8px 14px;}
.btn-save  > button{background:#f5f5f5;}
.btn-next  > button{background:#eef5ff;}
.btn-mark  > button{background:#ffddd5;}
/* SME grid */
.optgrid{display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin:6px 0;}
.rowgrid{display:grid; grid-template-columns: 1fr 1fr; gap:10px;}
/* Glossary drawer (from top) */
.drawer{position:sticky; top:0; z-index:10; background:#fff9e8; border:1px solid #e7d7a6;
        border-radius:12px; padding:10px; margin:8px 0 6px;}
/* Keep bottom slack minimal */
.btm{height:8px;}
</style>
""", unsafe_allow_html=True)

# =============== Helpers ===============
REQ_COLS = ["ID","Question (English)","Options (English)","Answer (English)","Explanation (English)",
            "Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)","QC_TA"]

def _txt(v): 
    if pd.isna(v): return ""
    return str(v).replace("\r\n","\n").strip()

def _split_opts(v):
    t=_txt(v)
    if not t: return ["","","",""]
    parts=re.split(r"\s*(?:\r?\n|\n|\r|\||[•;])\s*", t)
    parts=[p for p in parts if p]
    while len(parts)<4: parts.append("")
    return parts[:4]

def _clean_drive(url:str)->str:
    if "drive.google.com" not in url: return url
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def read_from_link(url:str)->pd.DataFrame:
    url=_clean_drive(url.strip())
    try: return pd.read_csv(url)
    except Exception: pass
    try: return pd.read_excel(url)
    except Exception as e:
        raise RuntimeError(f"Could not open link. Details: {e}")

def normalize_columns(df:pd.DataFrame)->pd.DataFrame:
    cols_lower={c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln=n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map={
        "ID": pick("ID","Id","id"),
        "Question (English)": pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)" : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"  : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"  : pick("Question (Tamil)","Q_TA","Tamil Question"),
        "Options (Tamil)"   : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"    : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)": pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA": pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
    }
    out=pd.DataFrame()
    for k in REQ_COLS:
        src=col_map.get(k)
        if src is None:
            out[k]="" if k=="QC_TA" else RuntimeError(f"Missing columns in the file: {k}")
            if isinstance(out[k], RuntimeError): raise out[k]
        else:
            out[k]=df[src]
    return out.reset_index(drop=True)

# =============== Session bootstrap ===============
ss=st.session_state
for k,v in [("qc_src",pd.DataFrame()),("qc_work",pd.DataFrame()),("qc_idx",0)]:
    if k not in ss: ss[k]=v

# =============== Header (date/id/time + buttons) ===============
today = dt.datetime.now()
ta_months = ["","ஜன","பிப்","மார்","ஏப்","மே","ஜூன்","ஜூலை","ஆக","செப்","அக்","நவ","டிச"]
ta_date = f"{today.day} {ta_months[today.month]} {today.year}  Oct {today.day}"
time_24 = today.strftime("%H:%M")

st.markdown('<div class="topbar">', unsafe_allow_html=True)
st.markdown(f"""
<div class="topgrid">
  <div class="badge">{ta_date}</div>
  <div style="text-align:center; color:#fff;">
     <div style="font-weight:700;">பாட பொருள் நிபுணர் பலகை / SME Panel</div>
     <div style="opacity:.9;">ID: {(_txt(ss.qc_work.iloc[ss.qc_idx]['ID']) if not ss.qc_work.empty else '—')}</div>
  </div>
  <div style="text-align:right; color:#fff; font-weight:600;">{time_24}</div>
</div>
""", unsafe_allow_html=True)

# header buttons (always visible)
colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("💾 Save", use_container_width=True):
        pass  # noop: all edits are in-place
with colB:
    if st.button("✅ Mark Complete", use_container_width=True):
        if not ss.qc_work.empty:
            ss.qc_work.at[ss.qc_idx,"QC_TA"]="✔"
with colC:
    if st.button("➡️ Save & Next", use_container_width=True):
        if not ss.qc_work.empty:
            ss.qc_idx = min(ss.qc_idx+1, len(ss.qc_work)-1)
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# =============== Compact Load Strip (10%) ===============
with st.container():
    link_col, load_col = st.columns([7,1])
    with link_col:
        link_in = st.text_input("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.",
                                placeholder="Paste the CSV/XLSX link", label_visibility="collapsed")
    with load_col:
        clicked_load = st.button("Load", use_container_width=True)

    up = st.file_uploader("Upload the file here (Limit 200 MB per file)", type=["csv","xlsx"], accept_multiple_files=False)

    if clicked_load:
        try:
            if link_in.strip():
                df = read_from_link(link_in)
            elif up is not None:
                df = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
            else:
                raise RuntimeError("Provide a link or upload a file.")
            df = normalize_columns(df)
            if "QC_TA" not in df.columns: df["QC_TA"]=""
            ss.qc_src = df.copy()
            ss.qc_work = df.copy()
            ss.qc_idx = 0
            st.success("Loaded.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

# Early exit if nothing loaded (SMEs will just see top strip)
if ss.qc_work.empty:
    st.stop()

# =============== Reference Panels (25% + 25%) ===============
row = ss.qc_work.iloc[ss.qc_idx]
def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br>"
        f"<b>Q:</b> {_txt(q)}<br>"
        f"<b>Options (A–D):</b> {_txt(op)}<br>"
        f"<b>Answer:</b> {_txt(ans)}<br>"
        f"<b>Explanation:</b> {_txt(exp)}"
    )
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

view_block("English Version / ஆங்கிலம்", row["Question (English)"], row["Options (English)"],
           row["Answer (English)"], row["Explanation (English)"], "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", row["Question (Tamil)"], row["Options (Tamil)"],
           row["Answer (Tamil)"], row["Explanation (Tamil)"], "ta")

st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்", help="Bottom block ~40% height")

# =============== Glossary drawer (top pop-down) ===============
def glossary_drawer():
    show = ss.get("show_glossary", False)
    if not show: return
    with st.container():
        st.markdown('<div class="drawer">', unsafe_allow_html=True)
        st.write("**📚 Glossary** — results for:", ss.get("glossary_query","—"))
        st.info("Hook this to your glossary CSV/Drive when ready. Render matches here.")
        if st.button("Close", key="g_close", help="Hide glossary"):
            ss.show_glossary=False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

glossary_drawer()   # safe (no args)

# =============== SME Editor (~40%) ===============
# Question (~2 lines)
q_key=f"q_{ss.qc_idx}"
a_key=f"a_{ss.qc_idx}"
b_key=f"b_{ss.qc_idx}"
c_key=f"c_{ss.qc_idx}"
d_key=f"d_{ss.qc_idx}"
ans_key=f"ans_{ss.qc_idx}"
exp_key=f"exp_{ss.qc_idx}"
for k,v in [
    (q_key, _txt(row["Question (Tamil)"])),
    (a_key, ""), (b_key, ""), (c_key,""), (d_key,""),
    (ans_key, _txt(row["Answer (Tamil)"])),
    (exp_key, _txt(row["Explanation (Tamil)"]))
]:
    if k not in ss: ss[k]=v

st.text_area(" ", key=q_key, height=72, label_visibility="collapsed", placeholder="கேள்வி / Question (TA)")

# Options grid (A,B / C,D)
A,B,C,D = _split_opts(row["Options (Tamil)"])
st.markdown('<div class="optgrid">', unsafe_allow_html=True)
st.text_input(" ", key=a_key, value=ss[a_key] or A, label_visibility="collapsed", placeholder="A")
st.text_input(" ", key=b_key, value=ss[b_key] or B, label_visibility="collapsed", placeholder="B")
st.text_input(" ", key=c_key, value=ss[c_key] or C, label_visibility="collapsed", placeholder="C")
st.text_input(" ", key=d_key, value=ss[d_key] or D, label_visibility="collapsed", placeholder="D")
st.markdown('</div>', unsafe_allow_html=True)

# Glossary field + Answer (same row)
gl, an = st.columns([1,1])
with gl:
    gq = st.text_input("சொல் அகராதி / Glossary", key=f"gq_{ss.qc_idx}", placeholder="(Type the word)")
    if st.button("Go", key=f"go_{ss.qc_idx}", use_container_width=True):
        ss.glossary_query = gq
        ss.show_glossary = True
        st.rerun()
with an:
    st.text_input("பதில் / Answer", key=ans_key, value=ss[ans_key], label_visibility="visible",
                  placeholder="A: …")

# Explanation (taller)
st.text_area("விளக்கங்கள் :", key=exp_key, height=180, value=ss[exp_key])

# Persist back into QC_TA merged text (for admin export)
def _merge(q,a,b,c,d,ans,exp):
    out=[]
    if _txt(q): out.append(f"Q: {_txt(q)}")
    ops=[_txt(a),_txt(b),_txt(c),_txt(d)]
    if any(ops):
        labels=list("ABCD")
        op_s=" | ".join([f"{labels[i]}) {ops[i]}" for i in range(4) if ops[i]])
        out.append(f"Options (A–D): {op_s}")
    if _txt(ans): out.append(f"Answer: {_txt(ans)}")
    if _txt(exp): out.append(f"Explanation: {_txt(exp)}")
    return "\n".join(out)

# autosave into QC_TA on every render (safe for iPad typing)
ss.qc_work.at[ss.qc_idx,"QC_TA"] = _merge(ss[q_key], ss[a_key], ss[b_key], ss[c_key], ss[d_key], ss[ans_key], ss[exp_key])

st.markdown('<div class="btm"></div>', unsafe_allow_html=True)
