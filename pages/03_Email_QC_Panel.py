# pages/03_Email_QC_Panel.py
from __future__ import annotations
import streamlit as st
import pandas as pd

# Local imports
from lib.top_strip import render_top_strip

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ---------- TOP STRIP (header + loader)
ready = render_top_strip()

# ---------- Helpers to read one row safely (column names may vary)
def _first_col(df: pd.DataFrame, names: list[str]) -> str:
    for n in names:
        if n in df.columns:
            val = df.at[idx, n]
            return "" if pd.isna(val) else str(val)
    return ""

def _options_line(df: pd.DataFrame, A, B, C, D) -> str:
    a = _first_col(df, A); b = _first_col(df, B); c = _first_col(df, C); d = _first_col(df, D)
    parts = [p for p in [a,b,c,d] if p]
    return " | ".join([f"{x}" for x in parts]) if parts else ""

# ---------- Render when dataset is ready
if not ready:
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()

ss = st.session_state
df: pd.DataFrame = ss.qc_df
idx: int = ss.qc_idx if "qc_idx" in ss else 0
idx = max(0, min(idx, len(df)-1))

# Guess common columns (adjust here to your sheet headers)
Q_ta  = _first_col(df, ["Q_ta","ta_Q","Q Tamil","Q (ta)","Q-TA"])
Q_en  = _first_col(df, ["Q_en","en_Q","Q English","Q (en)","Q-EN"])

A_ta  = _first_col(df, ["A_ta","ta_A","OptA_ta","OptionA_ta"])
B_ta  = _first_col(df, ["B_ta","ta_B","OptB_ta","OptionB_ta"])
C_ta  = _first_col(df, ["C_ta","ta_C","OptC_ta","OptionC_ta"])
D_ta  = _first_col(df, ["D_ta","ta_D","OptD_ta","OptionD_ta"])
A_en  = _first_col(df, ["A_en","en_A","OptA_en","OptionA_en"])
B_en  = _first_col(df, ["B_en","en_B","OptB_en","OptionB_en"])
C_en  = _first_col(df, ["C_en","en_C","OptC_en","OptionC_en"])
D_en  = _first_col(df, ["D_en","en_D","OptD_en","OptionD_en"])

Ans_ta = _first_col(df, ["Answer_ta","ta_Answer","Ans_ta","Answer TA"])
Ans_en = _first_col(df, ["Answer_en","en_Answer","Ans_en","Answer EN"])

Exp_ta = _first_col(df, ["Explanation_ta","ta_Explanation","Exp_ta","Explanation TA"])
Exp_en = _first_col(df, ["Explanation_en","en_Explanation","Exp_en","Explanation EN"])

# ---------- SME EDIT CONSOLE (FIRST)
st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

ecol1, ecol2 = st.columns([2,1])
with ecol1:
    q_val = st.text_area("", Q_ta, height=90, key=f"q_ta_{idx}", label_visibility="collapsed")
with ecol2:
    ans_val = st.text_input("பதில் / Answer", Ans_ta, key=f"ans_ta_{idx}")

ocol1, ocol2 = st.columns(2)
with ocol1:
    a_val = st.text_input("A", A_ta, key=f"A_ta_{idx}")
with ocol2:
    b_val = st.text_input("B", B_ta, key=f"B_ta_{idx}")
ocol3, ocol4 = st.columns(2)
with ocol3:
    c_val = st.text_input("C", C_ta, key=f"C_ta_{idx}")
with ocol4:
    d_val = st.text_input("D", D_ta, key=f"D_ta_{idx}")

st.text_area("விளக்கங்கள் :", Exp_ta, height=120, key=f"exp_ta_{idx}")

# Save buttons (top strip buttons are already present; these are optional duplicates)
# If you want these to mutate df, wire as needed:
# if st.button("Save changes"): ...

st.markdown("---")

# ---------- TAMIL ORIGINAL (REFERENCE)
st.markdown("#### Tamil Original / தமிழ் மூலப் பதிப்பு")
ta_box = st.container(border=True)
with ta_box:
    st.markdown(f"**Q:** {Q_ta or '—'}")
    st.markdown(f"**Options (A–D):** {_options_line(df, ['A_ta'], ['B_ta'], ['C_ta'], ['D_ta']) or '—'}")
    st.markdown(f"**Answer:** {Ans_ta or '—'}")
    st.markdown(f"**Explanation:** {Exp_ta or '—'}")

# ---------- ENGLISH ORIGINAL (REFERENCE)
st.markdown("#### English Version / ஆங்கிலம்")
en_box = st.container(border=True)
with en_box:
    st.markdown(f"**Q:** {Q_en or '—'}")
    st.markdown(f"**Options (A–D):** {_options_line(df, ['A_en'], ['B_en'], ['C_en'], ['D_en']) or '—'}")
    st.markdown(f"**Answer:** {Ans_en or '—'}")
    st.markdown(f"**Explanation:** {Exp_en or '—'}")
