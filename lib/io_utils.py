# lib/io_utils.py
import io
import os
import pandas as pd

def read_bilingual(file) -> pd.DataFrame:
    """Read csv/xlsx to DataFrame (header row is row 1)."""
    name = getattr(file, "name", "") or ""
    if name.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        try:
            df = pd.read_excel(file, engine="openpyxl")
        except Exception:
            df = pd.read_excel(file)
    return df if not df.empty else pd.DataFrame()

def export_qc(src_df: pd.DataFrame, work_df: pd.DataFrame, qc_map: dict):
    """Return (xlsx_bytes, csv_bytes) after replacing TA columns with QC edits."""
    if src_df is None or src_df.empty or work_df is None or work_df.empty or not qc_map:
        return None, None

    export_df = src_df.copy()

    # keys that may exist in work_df (created by ensure_work)
    repl = [("Q_TA","QC_Q_TA"), ("OPT_TA","QC_OPT_TA"), ("ANS_TA","QC_ANS_TA"), ("EXP_TA","QC_EXP_TA")]
    for base_key, qc_key in repl:
        src_col = qc_map.get(base_key)
        if src_col and qc_key in work_df.columns:
            export_df[src_col] = work_df[qc_key]

    # XLSX
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as w:
        export_df.to_excel(w, index=False)
    cbytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return xbuf.getvalue(), cbytes
