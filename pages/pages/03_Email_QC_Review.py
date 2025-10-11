# ================================
# 03_Email_QC_Review.py
# ================================

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Email QC Review", page_icon="✉️", layout="wide")
st.title("✉️ Email QC Review")
st.caption("View and review QC drafts for SME feedback.")

# Step 1 — Upload SME Allocation File
uploaded_file = st.file_uploader("Upload SME Allocation File (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.success(f"Loaded {len(df)} records from {uploaded_file.name}")
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    st.dataframe(df.head(), use_container_width=True)

    # Step 2 — Email Body Generator
    st.subheader("✉️ Generate QC Email")

    sme_names = df["SME Name"].unique().tolist() if "SME Name" in df.columns else []
    sme_choice = st.selectbox("Select SME", sme_names)

    if sme_choice:
        sme_rows = df[df["SME Name"] == sme_choice]
        subject = f"[QC Assignment] SME {sme_choice} - {len(sme_rows)} Questions Pending Review"
        deadline = (datetime.now().strftime("%d-%b-%Y"))
        email_body = f"""
Dear {sme_choice},

Greetings from **Make-A-Mark Academy**!

You have been assigned **{len(sme_rows)} questions** for bilingual QC verification.
Please review and update the Tamil translation where necessary.

Kindly return the verified file by **{deadline}**.

Best regards,  
**MAM Content Coordination Team**

---

🗂️ File: `{uploaded_file.name}`
📘 Subject/Unit: {sme_rows['Subject'].iloc[0] if 'Subject' in sme_rows.columns else 'N/A'}

---

_This is an auto-generated message for SME QC tracking._
        """

        st.text_area("Email Preview", email_body, height=250)
        st.download_button(
            "⬇️ Download Email Text",
            data=email_body.encode("utf-8"),
            file_name=f"email_{sme_choice}_QC.txt",
            mime="text/plain",
        )

else:
    st.info("Please upload a bilingual allocation file first.")
