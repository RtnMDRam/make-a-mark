# app.py — Mission Aspire SME Allocation (clean build, no Drive)
# Requirements: streamlit==1.38.0, pandas==2.2.2, openpyxl==3.1.5

from __future__ import annotations
import io, zipfile
from typing import List, Tuple
import pandas as pd
import streamlit as st

SAFE = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def sanitize(s: str) -> str:
    s = str(s or "").strip().replace(" ", "_")
    return "".join(ch for ch in s if ch in SAFE)

def base_name(subject: str, grade: str, unit: int, chap: int, lesson: str, bilingual=True) -> str:
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

def sme_filename(base: str, sme_name: str, start_row: int, end_row: int) -> str:
    clean_sme = sanitize(
        sme_name.replace("Mr.", "").replace("Mr", "")
                .replace("Dr.", "").replace("Dr", "")
                .replace("Mrs.", "").replace("Mrs", "")
                .replace("Ms.", "").replace("Ms", "")
                .strip()
    )
    return f"{base}__SME-{clean_sme}__rows-{start_row}-{end_row}.xlsx"

def read_uploaded(uploaded) -> pd.DataFrame:
    name = (uploaded.name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)
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

# ---------------- UI ----------------
st.set_page_config(page_title="Mission Aspire SME Allocation", layout="wide")
st.title("📘 Mission Aspire SME Allocation")
st.caption(
    "Upload the question bank and assign SMEs to row ranges. "
    "Returned QC files must keep the same name and append `__qc` before `.xlsx`."
)

with st.form("meta_form", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns(4)
    subject = c1.text_input("Subject", value="bio")
    grade   = c2.text_input("Grade", value="g11")
    unit    = c3.number_input("Unit #", min_value=0, value=4, step=1)
    chap    = c4.number_input("Chapter # (0 allowed)", min_value=0, value=9, step=1)
    lesson  = st.text_input("Lesson / short label (used in file name)", value="the_tissues")

    uploaded = st.file_uploader("Upload the master file (CSV or Excel)", type=["csv", "xlsx", "xls"])
    submitted = st.form_submit_button("Load file")

df = None
if submitted:
    if uploaded is None:
        st.error("Please upload a file to begin.")
    else:
        try:
            df = read_uploaded(uploaded)
            st.success(f"Loaded {len(df)} rows.")
            st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")

st.divider()

st.subheader("👩‍🏫 SME Details")
num_smes = st.number_input("Number of SMEs", min_value=1, max_value=20, value=1, step=1)
smes: List[Tuple[str, int, int]] = []

for i in range(int(num_smes)):
    st.markdown(f"**SME {i+1}**")
    c1, c2, c3 = st.columns([2,1,1])
    name = c1.text_input(f"Name for SME {i+1}", key=f"sme_name_{i}")
    start_row = c2.number_input(f"Start row for SME {i+1}", key=f"sme_start_{i}", min_value=1, value=1, step=1)
    end_row   = c3.number_input(f"End row for SME {i+1}", key=f"sme_end_{i}", min_value=1, value=1, step=1)
    smes.append((name, int(start_row), int(end_row)))

if st.button("📋 Show Allocation Summary"):
    st.subheader("✅ SME Allocation Summary")
    for i, (name, s, e) in enumerate(smes):
        st.write(f"**SME {i+1}: {name} → Rows {s} to {e}**")

st.markdown("")
left = st.columns([1,5])[0]
if left.button("📦 Generate SME Files (ZIP)", disabled=(df is None)):
    if df is None:
        st.warning("Please upload a master file first.")
    else:
        base = base_name(subject, grade, int(unit), int(chap), lesson, bilingual=True)
        out_files: List[Tuple[str, bytes]] = []

        for (name, s, e) in smes:
            if not name.strip():
                st.error("Every SME must have a name.")
                st.stop()
            if s > e:
                st.error(f"Invalid range for {name}: start({s}) > end({e}).")
                st.stop()

            lo = max(1, s)
            hi = max(1, e)
            part = df.iloc[lo-1:hi].copy()
            out_files.append((sme_filename(base, name, lo, hi), write_excel_bytes(part)))

        zip_bytes = build_zip(out_files)
        st.success(f"Generated {len(out_files)} SME files.")
        st.download_button(
            "⬇️ Download SME ZIP",
            data=zip_bytes,
            file_name=f"{base}__sme_split.zip",
            mime="application/zip",
        )

st.caption("Returned files after SME QC should append `__qc` before `.xlsx` (e.g., `...__rows-61-120__qc.xlsx`).")
