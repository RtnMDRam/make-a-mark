import streamlit as st

st.set_page_config(page_title="Mission Aspire", page_icon="🚀", layout="wide")
st.title("Mission Aspire")
st.write("Use the sidebar to open a page, or click a shortcut below.")

# Quick links to pages
st.page_link("pages/00_SME_Master.py", label="SME Master", icon="🧑‍🏫")
st.page_link("pages/01_Admin_View.py", label="Admin View", icon="📊")
st.page_link("pages/02_Email_QC_Generator.py", label="Email QC Generator", icon="✉️")
st.page_link("pages/04_Coordinator_Inbox.py", label="Coordinator Inbox", icon="📥")
st.page_link("pages/05_Drive_Link_Input.py", label="Drive Link Input", icon="🔗")

st.caption("All feature pages also appear in the left sidebar automatically.")
