# lib/io_utils.py (stub)
import io
import pandas as pd

def read_uploaded(up):
    """Return DataFrame from a CSV/XLSX upload; simple best-effort stub."""
    if up is None: return pd.DataFrame()
    name = up.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(up)
    try:
        return pd.read_excel(up, engine="openpyxl")
    except Exception:
        return pd.read_excel(up)

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
