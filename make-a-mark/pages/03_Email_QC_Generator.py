# pages/03_Email_QC_Generator.py
# ----------------------------------------
# Generates SME-specific email HTML blocks with QC status buttons

import streamlit as st
from urllib.parse import quote

st.set_page_config(page_title="Email QC Generator", page_icon="📧", layout="wide")
st.title("📧 SME Assignment Email Generator")
st.caption("Create QC assignment emails with pre-filled Start / Return / Help buttons.")

st.divider()

# ---- Inputs ----
col1, col2 = st.columns(2)
with col1:
    coordinator_email = st.text_input("Coordinator Email", "makeamark.inbox@gmail.com")
with col2:
    subject_prefix = st.text_input("Email Subject Prefix", "[QC ASSIGN]")

sme_name = st.text_input("SME Name", "Suganthi R.")
subject_token = st.text_input("Unique Token", "PHY-U1-CH2-SME04")
chapter_name = st.text_input("Lesson / Chapter", "Physics – Unit 1 – Motion of Pendulum")

# optional body notes
body_intro = st.text_area("Message to SME",
"""Dear {sme_name},

Please find attached the bilingual Question Bank file for QC verification.
Kindly review your allocated section and use the buttons below to update your status.

Thank you,
Make-A-Mark Academy Team
""", height=160)

# ---- Helper to build mailto buttons ----
def make_qc_buttons(email, token):
    def mailto(tag, body):
        return f"mailto:{email}?subject={quote(f'[{tag}] {token}')}&body={quote(body)}"
    return f"""
<p>
  <a href="{mailto('QC STARTED', 'QC work initiated. Will submit soon.')}"
     style="background:#ffe58f;color:#000;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600;margin-right:10px;">▶️ Start QC</a>
  <a href="{mailto('QC DONE', 'QC completed. File attached.')}"
     style="background:#b7f7b0;color:#000;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600;margin-right:10px;">✅ Return QC (attach file)</a>
  <a href="{mailto('QC HELP', 'Need assistance with QC or content clarification.')}"
     style="background:#e6f4ff;color:#000;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600;">❓ Need help</a>
</p>
"""

# ---- Generate preview ----
if st.button("Generate Email Template"):
    html_buttons = make_qc_buttons(coordinator_email, subject_token)
    full_body = body_intro.format(sme_name=sme_name) + "\n\n" + html_buttons
    subject_line = f"{subject_prefix} {subject_token} – {chapter_name}"

    st.success("✅ Email HTML generated below — copy and paste into Gmail Compose → ⋮ → Format → Plain/HTML.")
    st.write("**Subject:**", subject_line)
    st.markdown("---")
    st.markdown(full_body, unsafe_allow_html=True)
    st.markdown("---")
    st.code(full_body, language="html")

st.info("""
**Usage**
1️⃣ Enter SME details and click *Generate Email Template*  
2️⃣ Copy the generated HTML (bottom)  
3️⃣ Paste into Gmail/Outlook compose window  
4️⃣ Attach the bilingual file  
5️⃣ Send — Gmail filters will color messages automatically  
""")
