# pages/03_Email_QC_Panel.py
import streamlit as st
import re

# ========== STYLES ==========
CSS = """
<style>
:root{
  --ref-vh:20;        /* 20% viewport height each */
  --sep-top:#63d063;  /* green line SME→Tamil */
  --sep-mid:#4f92ff;  /* blue line Tamil→English */
}
.block-container{padding-top:10px !important; padding-bottom:10px !important;}
.qc-title{font-size:14px;font-weight:700;margin:0 0 6px 0;color:#e5e5e5;}
.qc-edit{height:36vh;border-radius:10px;background:rgba(255,255,255,0.04);margin-bottom:8px;}
.qc-hr{height:1px;border:0;margin:6px 0;}
.qc-hr.top{background:var(--sep-top);}
.qc-hr.mid{background:var(--sep-mid);}
.qc-ref{
  height:calc(var(--ref-vh)*1vh);
  overflow:auto;
  font-size:16px;
  line-height:1.35;
  color:#eaeaea;
  padding:4px 8px;
  text-align:justify;
}
.qc-ref p{margin:4px 0;}
.qc-label{font-size:12px;opacity:0.8;margin-bottom:4px;}
</style>
"""

# ========== HELPERS ==========
def clean_text(s):
    if not s: return ""
    s=str(s).replace("\\r"," ").replace("\\n"," ")
    s=re.sub(r"\s+"," ",s).replace("**","")
    return s.strip()

def pick(row, keys):
    for k in keys:
        if k in row and str(row[k]).strip() not in ("","nan","None"):
            return clean_text(row[k])
    return ""

def tamil_html(row):
    q=pick(row,["ta.q","ta_q","taQuestion","question_ta"])
    o=pick(row,["ta.o","ta_o","taOptions","options_ta"])
    a=pick(row,["ta.a","ta_a","taAnswer","answer_ta"])
    e=pick(row,["ta.e","ta_e","taExplanation","explanation_ta"])
    html=["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: html.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: html.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: html.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(html)==1: html.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(html)

def english_html(row):
    q=pick(row,["en.q","en_q","question","Question","question_en"])
    o=pick(row,["en.o","en_o","options","Options","questionOptions"])
    a=pick(row,["en.a","en_a","answer","Answer","answers"])
    e=pick(row,["en.e","en_e","explanation","Explanation","explanations"])
    html=["<div class='qc-label'>English Version</div>"]
    if q: html.append(f"<p><b>Q :</b> {q}</p>")
    if o: html.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>Answer :</b> {a}</p>")
    if e: html.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(html)==1: html.append("<p><i>(English columns missing)</i></p>")
    return "".join(html)

# ========== MAIN ==========
st.set_page_config(page_title="SME QC Panel", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

df = st.session_state.get("qc_df")

if df is None or len(df)==0:
    st.info("Please upload and Load a file first.")
else:
    row = df.iloc[0].to_dict()
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{tamil_html(row)}</div>", unsafe_allow_html=True)
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{english_html(row)}</div>", unsafe_allow_html=True)

    with st.expander("Debug Columns"):
        st.write(list(df.columns))
