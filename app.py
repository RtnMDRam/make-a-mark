# =========================
# Make-A-Mark Streamlit App
# =========================

import streamlit as st

st.set_page_config(
    page_title="Make-A-Mark Academy",
    page_icon="🎓",
    layout="wide"
)

# Introductory block — displayed before the main dashboard
st.markdown("""
# 🎓 **Make-A-Mark Academy**
### Mission Aspire | Bilingual NEET & JEE Program
st.caption("**மேக்-அ-மார்க் அகாடமி – தாய் மொழி கல்வித் தளம் (ஆங்கிலம்–தமிழ்)**")

Welcome to the **Admin & Content Processing Dashboard**.  
This platform enables centralized monitoring and bilingual content management for
NEET and JEE preparation across participating institutions.

**Key Modules:**
- 🧑‍🏫 **SME Allocation Dashboard** – Assign, track, and manage content contributors.  
  *ஆசிரியர்கள் ஒதுக்கீட்டு பலகை*  

- 📘 **Question Bank Processor** – Generate bilingual (English–Tamil) datasets.  
  *தமிழ் மொழி / கேள்விகளின் தொகுப்பு செயலி*  

- 🧾 **Reports Panel** – Export SME work summaries and progress metrics.  
  *அறிக்கைகள் & முன்னேற்றக் கண்காணிப்பு பலகை*    

---
""")

from __future__ import annotations
import io
import zipfile
from typing import List, Tuple

import pandas as pd
import streamlit as st

# ------------------------------ utils ------------------------------
SAFE = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def sanitize(s: str) -> str:
    s = str(s or "").strip().replace(" ", "_")
    return "".join(ch for ch in s if ch in SAFE)

def base_name(subject: str, grade: str, unit: int, chap: int, lesson: str, bilingual=True) -> str:
    """
    bl_ for bilingual, mam_ for Tamil-only. chap can be 0.
    Example: bl_bio_g11_unit_4_chap_9_the_tissues_qb
    """
    prefix = "bl" if bilingual else "mam"
    parts = [
        prefix,
        sanitize(subject.lower()),
        sanitize(grade.lower()),
        "unit", str(unit),
        "chap", str(chap),
        sanitize(lesson.lower()),
        "qb",
    ]
    return "_".join(parts)

def strip_salutation(name: str) -> str:
    n = (name or "").replace(".", " ").strip()
    for tok in ["Mr", "Mrs", "Ms", "Dr", "Prof", "Sir", "Madam", "Sri", "Smt"]:
        if n.lower().startswith(tok.lower()+" "):
            n = n[len(tok):].strip()
    return n

def sme_filename(base: str, sme_name: str, start_row: int, end_row: int) -> str:
    clean = sanitize(strip_salutation(sme_name))
    return f"{base}__SME-{clean}__rows-{start_row}-{end_row}.xlsx"

def read_uploaded(uploaded) -> pd.DataFrame:
    name = (uploaded.name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)          # needs openpyxl
    return pd.read_csv(uploaded)

def write_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name=sheet_name)
    buf.seek(0)
    return buf.read()

def build_zip(files: List[Tuple[str, bytes]]) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files:
            zf.writestr(fname, content)
    mem.seek(0)
    return mem.read()

# ------------------------------ UI ------------------------------
st.set_page_config(page_title="Make-a-Mark — SME Allocation", layout="wide")
st.title("✍️ Make-a-Mark — SME Allocation (offline)")
st.caption("Upload the master file, assign SMEs by row ranges, download a ZIP of per-SME Excel files. "
           "Returned QC files should keep the same name and append `__qc` before `.xlsx`.")

with st.form("meta", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns(4)
    subject = c1.text_input("Subject", value="bio")
    grade   = c2.text_input("Grade", value="g11")
    unit    = c3.number_input("Unit #", min_value=0, value=4, step=1)
    chap    = c4.number_input("Chapter # (0 allowed)", min_value=0, value=9, step=1)
    lesson  = st.text_input("Lesson / short label (used in file name)", value="the_tissues")

    uploaded = st.file_uploader("Upload the master file (CSV or Excel)", type=["csv","xlsx","xls"])
    submitted = st.form_submit_button("Load file")

df = None
if submitted:
    if uploaded is None:
        st.error("Please upload a file to begin.")
    else:
        try:
            df = read_uploaded(uploaded)
            st.success(f"Loaded {len(df)} rows.")
            st.dataframe(df.head(12), use_container_width=True)
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")

st.markdown("---")

# SME ranges
st.subheader("👩‍🏫 SME Details")
num_smes = st.number_input("Number of SMEs", min_value=1, max_value=20, step=1, value=1)
smes: List[Tuple[str, int, int]] = []

for i in range(int(num_smes)):
    st.markdown(f"**SME {i+1}**")
    c1, c2, c3 = st.columns([2,1,1])
    name = c1.text_input(f"Name for SME {i+1}", key=f"sme_name_{i}")
    start_row = c2.number_input(f"Start row for SME {i+1}", key=f"sme_start_{i}", min_value=1, step=1, value=1)
    end_row   = c3.number_input(f"End row for SME {i+1}", key=f"sme_end_{i}",   min_value=1, step=1, value=1)
    smes.append((name, int(start_row), int(end_row)))

if st.button("📋 Show Allocation Summary"):
    st.subheader("✅ SME Allocation Summary")
    for i, (name, s, e) in enumerate(smes):
        st.write(f"**SME {i+1}: {name or '—'} → Rows {s} to {e}**")

# Generate ZIP
st.markdown("")
left = st.columns([1,5])[0]
if left.button("📦 Generate SME Files (ZIP)", disabled=(df is None)):
    if df is None:
        st.warning("Please upload a master file first.")
    else:
        base = base_name(subject, grade, int(unit), int(chap), lesson, bilingual=True)

        out_files: List[Tuple[str, bytes]] = []
        for (name, s, e) in smes:
            if not (name or "").strip():
                st.error("Every SME must have a name.")
                st.stop()
            if s > e:
                st.error(f"Invalid range for {name}: start({s}) > end({e}).")
                st.stop()
            # 1-based inclusive → 0-based slice
            lo = max(1, s)
            hi = max(1, e)
            slice_df = df.iloc[lo-1:hi].copy()
            fname = sme_filename(base, name, lo, hi)
            out_files.append((fname, write_excel_bytes(slice_df)))

        zip_bytes = build_zip(out_files)
        st.success(f"Generated {len(out_files)} SME files.")
        st.download_button(
            "⬇️ Download SME ZIP",
            data=zip_bytes,
            file_name=f"{base}__sme_split.zip",
            mime="application/zip",
        )

st.caption("Returned files after SME QC should keep the same name and append `__qc` before `.xlsx` "
           "(e.g., `...__rows-61-120__qc.xlsx`).")
