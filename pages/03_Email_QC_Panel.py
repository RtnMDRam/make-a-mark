# pages/03_Email_QC_Panel.py
# SME-only, single-page iPad layout
# - No Streamlit sidebar or chrome
# - Top 5% compact header (ID, progress, Prev/Next)
# - Middle: EN original + TA original (read-only)
# - Bottom 50%: SME Edit Console (Tamil) with live preview + save
# - Sticky 5% footer: paste link from email and Load (CSV/XLSX; supports Google Drive links)

import re
import io
import pandas as pd
import streamlit as st

# ---------- Page + chrome hiding ----------
st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
/* Hide Streamlit chrome and sidebar toggles */
[data-testid="stSidebar"]{display:none;}
[data-testid="collapsedControl"]{display:none;}
header, footer, .stAppToolbar {visibility:hidden; height:0;}

/* Body padding so sticky footer doesn't overlap content */
main .block-container {padding-bottom: 110px;}

/* Sticky footer (link loader) ~5% of iPad vertical) */
.sme-footer {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
  background: rgba(30,30,30,0.96);
  border-top: 1px solid #333; padding: 10px 14px;
}
.sme-footer .wrap {max-width: 1200px; margin: 0 auto;}
.sme-footer label, .sme-footer p {color: #ddd !important; margin: 0 0 6px 2px; font-size: 0.9rem;}
.sme-footer .note {color:#9ad27f !important;}

.box {border:1px solid #d9d9d9; border-radius:12px; padding:14px 16px; margin:10px 0;}
.box.en {background:#eaf2ff; border-color:#9cc4ff;}
.box.ta {background:#eaf7ec; border-color:#8ed39a;}
.box.preview {background:#fffbe6; border-color:#ffe58f;}

h4.title {margin:0 0 10px 0;}
.label {display:inline-block; background:#eef1f3; padding:2px 8px; border-radius:6px; font-size:0.9rem;}
.hr {height:8px;}
</style>
""", unsafe_allow_html=True)

# ---------- Columns expected ----------
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA"
]

# ---------- Helpers ----------
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
    """Turn common Google Drive share links into direct-download."""
    if "drive.google.com" not in url: return url
    # patterns:
    # https://drive.google.com/file/d/<ID>/view?usp=...  -> https://drive.google.com/uc?export=download&id=<ID>
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    # https://drive.google.com/open?id=<ID>
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def read_from_link(link:str)->pd.DataFrame:
    link=_clean_drive(link.strip())
    # try CSV then Excel
    try:
        return pd.read_csv(link)
    except Exception:
        pass
    try:
        return pd.read_excel(link)
    except Exception as e:
        raise RuntimeError(f"Could not open link. Expecting CSV/XLSX. Details: {e}")

# ---------- Session defaults ----------
ss = st.session_state
if "qc_src" not in ss:   ss.qc_src = pd.DataFrame()
if "qc_work" not in ss:  ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss:   ss.qc_idx = 0
if "load_link" not in ss: ss.load_link = ""

# ---------- Sticky footer (paste link + load) ----------
with st.container():
    st.markdown('<div class="sme-footer"><div class="wrap">', unsafe_allow_html=True)
    f1,f2 = st.columns([6,1])
    with f1:
        ss.load_link = st.text_input("Paste file link here (CSV/XLSX • Google Drive or direct URL)", value=ss.load_link, key="link_in")
        st.markdown('<p class="note">Paste the link from your email and press <b>Load</b>. The page fills automatically.</p>', unsafe_allow_html=True)
    with f2:
        if st.button("Load", use_container_width=True):
            try:
                df = read_from_link(ss.load_link)
                # If admin used different headers, try to auto-map by fuzzy names
                cols_lower = {c.lower(): c for c in df.columns}
                def pick(*names):
                    for n in names:
                        if n in df.columns: return n
                        if n.lower() in cols_lower: return cols_lower[n.lower()]
                    return None

                # Build a normalized frame
                col_map = {
                    "ID": pick("ID","Id","id"),
                    "Question (English)": pick("Question (English)","Q_EN","Question_English","English Question"),
                    "Options (English)":  pick("Options (English)","OPT_EN","Options_English"),
                    "Answer (English)":   pick("Answer (English)","ANS_EN","Answer_English"),
                    "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
                    "Question (Tamil)":   pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
                    "Options (Tamil)":    pick("Options (Tamil)","OPT_TA","Options_Tamil"),
                    "Answer (Tamil)":     pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
                    "Explanation (Tamil)":pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
                    "QC_TA":              pick("QC_TA","QC Verified (Tamil)","QC_Tamil")
                }
                missing = [k for k,v in col_map.items() if v is None]
                if missing:
                    raise RuntimeError("Missing columns in the file: " + ", ".join(missing))

                normalized = df[[col_map[k] for k in col_map]].copy()
                normalized.columns = list(col_map.keys())
                ss.qc_src = normalized.reset_index(drop=True)
                ss.qc_work = ss.qc_src.copy()
                ss.qc_idx = 0
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))
    st.markdown('</div></div>', unsafe_allow_html=True)

# ---------- If nothing loaded yet, stop (SME sees blank workspace above footer) ----------
if ss.qc_work.empty:
    st.stop()

# ---------- Current row ----------
row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

# ---------- Compact header (~5%) ----------
h1,h2,h3 = st.columns([2,4,2])
with h1:
    st.markdown("## 📝 SME QC Panel")
with h2:
    st.caption(f"English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)} · ID: {rid}")
    st.progress((ss.qc_idx+1)/max(1,len(ss.qc_work)))
with h3:
    cprev, cnext = st.columns(2)
    with cprev:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx -= 1
            st.experimental_rerun()
    with cnext:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx += 1
            st.experimental_rerun()

st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

# ---------- Reference panels ----------
en_q,en_op,en_ans,en_exp = [_txt(row[c]) for c in ["Question (English)","Options (English)","Answer (English)","Explanation (English)"]]
ta_q,ta_op,ta_ans,ta_exp = [_txt(row[c]) for c in ["Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)"]]

def view_block(title, q, op, ans, exp, cls):
    html = (
        f"<span class='label'>{title}</span><br><br>"
        f"<b>Q:</b> {q}<br>"
        f"<b>Options (A–D):</b> {op}<br>"
        f"<b>Answer:</b> {ans}<br>"
        f"<b>Explanation:</b> {exp}"
    )
    st.markdown(f"<div class='box {cls}'>{html}</div>", unsafe_allow_html=True)

view_block("English Version / ஆங்கிலம்", en_q, en_op, en_ans, en_exp, "en")
view_block("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q, ta_op, ta_ans, ta_exp, "ta")

# ---------- SME Edit Console (bottom ~50%) ----------
st.markdown("<h4 class='title'>SME Edit Console / ஆசிரியர் திருத்தம்</h4>", unsafe_allow_html=True)
A,B,C,D = _split_opts(ta_op)
rowkey = f"r{ss.qc_idx}"
# set per-row sticky defaults
for key,val in [(f"q_{rowkey}",ta_q),(f"a_{rowkey}",A),(f"b_{rowkey}",B),(f"c_{rowkey}",C),(f"d_{rowkey}",D),(f"ans_{rowkey}",ta_ans),(f"exp_{rowkey}",ta_exp)]:
    if key not in ss: ss[key]=val

q_val   = st.text_area("கேள்வி / Question (TA)", value=ss[f"q_{rowkey}"], key=f"q_in_{rowkey}", height=90)
c1,c2   = st.columns(2)
with c1:
    a_val = st.text_input("A", value=ss[f"a_{rowkey}"], key=f"a_in_{rowkey}")
    c_val = st.text_input("C", value=ss[f"c_{rowkey}"], key=f"c_in_{rowkey}")
with c2:
    b_val = st.text_input("B", value=ss[f"b_{rowkey}"], key=f"b_in_{rowkey}")
    d_val = st.text_input("D", value=ss[f"d_{rowkey}"], key=f"d_in_{rowkey}")
ans_val = st.text_input("பதில் / Answer", value=ss[f"ans_{rowkey}"], key=f"ans_in_{rowkey}")
exp_val = st.text_area("விளக்கம் / Explanation", value=ss[f"exp_{rowkey}"], key=f"exp_in_{rowkey}", height=120)

# Live preview
preview = build_ta_text(q_val, a_val, b_val, c_val, d_val, ans_val, exp_val)
st.markdown(f"<div class='box preview'><span class='label'>Live Preview / நேரடி முன்னோட்டம்</span><br><br>{preview}</div>", unsafe_allow_html=True)

# Save controls
b1,b2 = st.columns([1,2])
with b1:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = preview
        st.success("Saved.")
with b2:
    if st.button("💾 Save & Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = preview
        ss.qc_idx += 1
        st.experimental_rerun()
