import streamlit as st
from datetime import datetime

# --- Hide Streamlit sidebar and menu (copy/paste this very first) ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Tamil calendar and color setup ---
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

now = datetime.now()
tamil_date = tamil_month_day(now)      # Tamil month and date in quotes
eng_date = now.strftime("“%Y %b %d”") # English date in quotes
time_24 = now.strftime("“%H:%M”")     # Time in quotes

TOTAL_QUESTIONS = 100
answered = 25
remaining = TOTAL_QUESTIONS - answered
row_id = 38

# --- Top Bar/Buttons (button area improved for spacing) ---
st.markdown(
    f"""
    <div style="background:{PRIMARY_HEADER};padding:16px 12px 8px 12px;border-radius:15px 15px 0px 0px;box-shadow:0 3px 16px #e0e8ef44;">
        <div style="display:flex;flex-wrap:wrap;flex-direction:row;align-items:center;justify-content:space-between;gap:6px;">
            <div style="font-size:1.1rem;font-weight:700;color:#fff;">
                {tamil_date} / {eng_date} &nbsp;&nbsp;{time_24}
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
                <button style="background:{MINT};color:#414062;border:none;padding:6px 18px;font-weight:700;border-radius:7px;">Hi! Glossary</button>
                <button style="background:{YELLOW};color:#513c00;border:none;padding:6px 18px;font-weight:700;border-radius:7px;">Save & Cont..</button>
                <span style="background:{OFF_WHITE};color:#444;padding:7px 13px 7px 13px;border-radius:5px 0 0 5px;border:1px solid {SOFT_LAVENDER};">25</span>
                <span style="background:{MILD_PURPLE};color:#fff;font-weight:bold;padding:7px 13px;">ID 38</span>
                <span style="background:{OFF_WHITE};color:#444;padding:7px 13px 7px 13px;border-radius:0 5px 5px 0;border:1px solid {SOFT_LAVENDER};">75</span>
                <button style="background:{SOFT_ACCENT};color:#692d67;border:none;padding:6px 18px;font-weight:700;border-radius:7px;">Save & Next</button>
                <button style="background:{SOFT_LAVENDER};color:#444;padding:6px 18px;font-weight:700;border:none;border-radius:7px;">Save File</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True
)

st.markdown(
    f"<div style='background:{PASTEL_BG}; border-radius:0 0 18px 18px; padding:18px 24px;'>", unsafe_allow_html=True
)

# === Editable SME Tamil Area ===
st.markdown(f"<div style='background:{LIGHT_BLUE};padding:10px;border-radius:13px;margin-bottom:15px;'>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#6A4C93;font-weight:bold;'>Subject Matter Expert Space — Editable</h4>", unsafe_allow_html=True)

q_text = st.text_area("கேள்வி :", height=65)
cols_opt = st.columns(2)
with cols_opt[0]:
    opt_a = st.text_input("தேர்வு A (Option A)", key="opt_a")
    opt_b = st.text_input("தேர்வு B (Option B)", key="opt_b")
with cols_opt[1]:
    opt_c = st.text_input("தேர்வு C (Option C)", key="opt_c")
    opt_d = st.text_input("தேர்வு D (Option D)", key="opt_d")

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

explanation = st.text_area("விளக்கங்கள் :", height=45)

st.markdown("</div>", unsafe_allow_html=True)  # End SME Edit Box

# === Reference Panels: English (Top), Tamil (Bottom) ===
st.markdown(
    f"<div style='border-radius:13px;background:{OFF_WHITE};margin:0 0 20px 0;padding:10px 14px 13px 14px;box-shadow:0 3px 10px #e2e6f399;'>", unsafe_allow_html=True
)
st.markdown("""
<b>English (read-only)</b><br>
<b>Question:</b> Specialized pits called bordered pits are present on the radial walls of<br>
<b>Options (A–D):</b><br>
A) Xylem tracheids.<br>
B) Sieve tubes.<br>
C) Xylem fibers.<br>
D) Sieve plates.<br>
<b>Answer:</b> A) Xylem tracheids.<br>
<b>Explanation:</b><br>
Bordered pits are cavities in the lignified cell walls of the xylem. (...)<br>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"<div style='border-radius:13px;background:{OFF_WHITE};margin:0 0 10px 0;padding:10px 14px 13px 14px;'>", unsafe_allow_html=True
)
st.markdown("""
<b>தமிழ் — படிக்க மட்டும் — Original</b><br>
<b>கேள்வி:</b> எல்லைப்பட்ட குடிகள் எனப்படும் சிறப்பு குடிகள் ...<br>
<b>விருப்பங்கள்:</b><br>
A) சைலம் மூச்சுக்குழாய்கள்.<br>
B) குழாய்களை சல்லடை செய்யும்.<br>
C) சைலம் இழைகள்.<br>
D) தட்டுகளை சல்லடை செய்யும்.<br>
<b>பதில்:</b> A) சைலம் மூச்சுக்குழாய்கள்.<br>
<b>விளக்கம்:</b><br>
சைலத்தின் லிக்னின்டைக் ...<br>
""", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

st.info("All displayed fields and color blocks are fully touch-optimized for iPad use. Buttons, inputs, and backgrounds use harmonious pastels from your chosen theme. Function logic and database integration can follow as your next step.")
