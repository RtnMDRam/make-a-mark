 import streamlit as st
import pandas as pd
from datetime import datetime

# --- Hide Streamlit sidebar and menu ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def tamil_month_day(dt):
    tamil_months = [
        "சித்திரை", "வைகாசி", "ஆணி", "ஆடி", "ஆவணி", "புரட்டாசி",
        "ஐப்பசி", "கார்த்திகை", "மார்கழி", "தை", "மாசி", "பங்குனி"
    ]
    tamil_month = tamil_months[(dt.month-4)%12]
    return f"“{tamil_month} {dt.day}”"

PASTEL_BG = "#F9F9FB"
PRIMARY_HEADER = "#A597F3"
SOFT_ACCENT = "#F9D5FF"
MINT = "#C0DAE5"
MILD_PURPLE = "#BCB2DB"
LIGHT_BLUE = "#D1F1FF"
SOFT_LAVENDER = "#C4B5D1"
YELLOW = "#F6D9B7"
OFF_WHITE = "#FFFDFB"

st.set_page_config(page_title="SME Panel", layout="wide")

# === File upload or sample dataset ===
uploaded_file = st.file_uploader("🔼 Upload bilingual Excel (.xlsx)", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("File loaded! Edit questions below.")
else:
    st.info("No file uploaded! Using sample questions. Upload a bilingual Excel file anytime.")
    df = pd.DataFrame({
        "question": ["Sample: What is a cell?", "Sample: Explain tissue organization."],
        "கேள்வி": ["உதாரணம்: ஒரு செல் என்றால் என்ன?", "உதாரணம்: திசு அமைப்பு விளக்குக."]
    })

if 'edited_tamil' not in st.session_state:
    st.session_state.edited_tamil = list(df["கேள்வி"])
if 'row_index' not in st.session_state:
    st.session_state.row_index = 0

row_idx = st.session_state.row_index
total_questions = len(df)

now = datetime.now()
tamil_date = tamil_month_day(now)
eng_date = now.strftime("“%Y %b %d”")
time_24 = now.strftime("“%H:%M”")

st.markdown(
    f"""
    <div style="background:{PRIMARY_HEADER};padding:14px 12px 6px 12px;border-radius:13px 13px 0 0;box-shadow:0 3px 16px #e0e8ef44;">
        <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px;">
            <div style="font-size:1.05rem;font-weight:700;color:#fff;">
                {tamil_date} / {eng_date} &nbsp;&nbsp;{time_24}
            </div>
            <div style="display:flex;gap:7px;">
                <button style="background:{MINT};color:#414062;border:none;padding:6px 18px;font-weight:700;border-radius:7px;">Glossary</button>
                <span style="background:{OFF_WHITE};color:#444;padding:7px 13px 7px 13px;border-radius:5px 0 0 5px;border:1px solid {SOFT_LAVENDER};">{row_idx+1}</span>
                <span style="background:{MILD_PURPLE};color:#fff;font-weight:bold;padding:7px 13px;">ID {row_idx+1}</span>
                <span style="background:{OFF_WHITE};color:#444;padding:7px 13px 7px 13px;border-radius:0 5px 5px 0;border:1px solid {SOFT_LAVENDER};">{total_questions-row_idx}</span>
                <button style="background:{SOFT_ACCENT};color:#692d67;border:none;padding:6px 18px;font-weight:700;border-radius:7px;">Save & Next</button>
                <button style="background:{SOFT_LAVENDER};color:#444;padding:6px 18px;font-weight:700;border:none;border-radius:7px;">Save File</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True
)

st.markdown(f"<div style='background:{PASTEL_BG}; border-radius:0 0 18px 18px; padding:18px 24px;'>", unsafe_allow_html=True)

st.markdown(f"<div style='background:{LIGHT_BLUE};padding:10px;border-radius:13px;margin-bottom:15px;'>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#6A4C93;font-weight:bold;'>பொருள் தரம் தேர்வு இடம் — SME Editable</h4>", unsafe_allow_html=True)

edited_tamil = st.text_area("கேள்வி :", value=st.session_state.edited_tamil[row_idx], height=65)
if st.button("Save Edit"):
    st.session_state.edited_tamil[row_idx] = edited_tamil
    st.success("Saved edit for this question.")

cols_opt = st.columns(2)
with cols_opt[0]:
    opt_a = st.text_input("தேர்வு A (Option A)", value="", key="opt_a")
    opt_b = st.text_input("தேர்வு B (Option B)", value="", key="opt_b")
with cols_opt[1]:
    opt_c = st.text_input("தேர்வு C (Option C)", value="", key="opt_c")
    opt_d = st.text_input("தேர்வு D (Option D)", value="", key="opt_d")

st.markdown(
    f"""
    <div style="display:flex;flex-direction:row;align-items:center;background:{SOFT_LAVENDER};padding:10px;margin:17px 0 0 0;border-radius:9px;">
        <div style="flex:2;">
            <label style="font-weight:bold;color:#402a4c;margin-right:9px;">சொல் அகராதி / Glossary</label>
            <input type="text" style="width:65%;padding:7px;border-radius:7px;border:1px solid {PASTEL_BG};">
        </div>
        <div style="flex:1;display:flex;align-items:center;">
            <label style="font-weight:600;color:#495;">சரியான பதில் / Correct Answer&nbsp;:</label>
            <select style="border-radius:6px;border:1px solid #cdd3eb;padding:5px 15px;">
                <option>A</option>
                <option>B</option>
                <option>C</option>
                <option>D</option>
            </select>
        </div>
    </div>
    """, unsafe_allow_html=True
)

explanation = st.text_area("விளக்கங்கள் :", value="", height=45)
st.markdown("</div>", unsafe_allow_html=True)  # End SME Edit Box

st.markdown(
    f"<div style='border-radius:13px;background:{OFF_WHITE};margin:0 0 20px 0;padding:10px 14px 13px 14px;box-shadow:0 3px 10px #e2e6f399;'>", unsafe_allow_html=True
)
st.markdown(f"""
<b>English (read-only)</b><br>
<b>Question:</b> {df.loc[row_idx, 'question']}<br>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='border-radius:13px;background:{OFF_WHITE};margin:0 0 10px 0;padding:10px 14px 13px 14px;'>", unsafe_allow_html=True
)
st.markdown(f"""
<b>தமிழ் — படிக்க மட்டும் — Original</b><br>
<b>கேள்வி:</b> {df.loc[row_idx, 'கேள்வி']}<br>
""", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if row_idx > 0:
        if st.button("Previous"):
            st.session_state.row_index -= 1
with col2:
    if row_idx < len(df) - 1:
        if st.button("Next"):
            st.session_state.row_index += 1

if st.button("Finish"):
    df["கேள்வி"] = st.session_state.edited_tamil
    df.to_excel("SME_Reviewed_bilingual.xlsx", index=False)
    st.success("All edits saved locally as SME_Reviewed_bilingual.xlsx.")

st.info("All displayed fields and color blocks are touch-optimized for iPad. You can always upload your Excel file or work with sample questions.")

