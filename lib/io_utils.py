# lib/io_utils.py
import io
import os
import pandas as pd

def read_bilingual(uploaded_file) -> pd.DataFrame:
    """Read CSV/XLSX with header row preserved; return DataFrame."""
    name = (uploaded_file.name or "").lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        # try openpyxl first but fall back if missing
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception:
            df = pd.read_excel(uploaded_file)
    return df

def export_qc(src_df: pd.DataFrame, qc_work: pd.DataFrame, qc_map: dict):
    """
    Create XLSX/CSV bytes by replacing TA columns in a copy of src_df with QC_* columns
    from qc_work, while preserving original header names and order.
    qc_map keys: ['Q_TA','OPT_TA','ANS_TA','EXP_TA'] mapped to actual column names in src.
    qc_work must contain ['QC_Q_TA','QC_OPT_TA','QC_ANS_TA','QC_EXP_TA'].
    """
    if src_df.empty or not qc_map:
        return None, None

    out = src_df.copy()
    repl = [
        ("Q_TA",   "QC_Q_TA"),
        ("OPT_TA", "QC_OPT_TA"),
        ("ANS_TA", "QC_ANS_TA"),
        ("EXP_TA", "QC_EXP_TA"),
    ]
    for base_key, qc_key in repl:
        src_col = qc_map.get(base_key)
        if src_col and qc_key in qc_work.columns:
            out[src_col] = qc_work[qc_key]

    # XLSX
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as w:
        out.to_excel(w, index=False)
    xlsx_bytes = xbuf.getvalue()

    # CSV (UTF-8 with BOM so Tamil stays intact in Excel)
    csv_bytes = out.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return xlsx_bytes, csv_bytes
