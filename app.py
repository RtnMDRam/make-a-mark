import streamlit as st
import pandas as pd

# Load bilingual Excel
df = pd.read_excel("bl_bio_bot_unit_4_chap_9_the_tissues_qb.xlsx")

if 'edited_tamil' not in st.session_state:
    st.session_state.edited_tamil = list(df["கேள்வி"])
if 'row_index' not in st.session_state:
    st.session_state.row_index = 0

row_idx = st.session_state.row_index
st.markdown(f"#### Question {row_idx + 1} of {len(df)}")

# Editable top box (pre-fill from Tamil column)
st.subheader("Editable Tamil Area (Top)")
edited_value = st.text_area("Edit Tamil (SME Review)", value=st.session_state.edited_tamil[row_idx])
if st.button("Save Edit"):
    st.session_state.edited_tamil[row_idx] = edited_value

# Middle: Reference Tamil (original from Excel)
st.subheader("Reference Tamil Content (Middle)")
st.info(df.loc[row_idx, "கேள்வி"])

# Bottom: Reference English (from Excel)
st.subheader("English Content (Bottom)")
st.success(df.loc[row_idx, "question"])

# Navigation buttons
col1, col2 = st.columns([1, 1])
with col1:
    if row_idx > 0:
        if st.button("Previous"):
            st.session_state.row_index -= 1
with col2:
    if row_idx < len(df) - 1:
        if st.button("Next"):
            st.session_state.row_index += 1

# Finish button for export/upload
if st.button("Finish"):
    # Save all SME-edited Tamil to Excel
    df["கேள்வி"] = st.session_state.edited_tamil
    df.to_excel("SME_Reviewed_bilingual.xlsx", index=False)
    st.success("All edits saved locally as SME_Reviewed_bilingual.xlsx. (Google Drive upload can be automated next)")
