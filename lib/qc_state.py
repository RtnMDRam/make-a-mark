# lib/qc_state.py (stub)
import streamlit as st
import pandas as pd

REQUIRED = ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]

def ensure_session_keys(ss=None):
    ss = ss or st.session_state
    for k, v in {
        "qc_src": pd.DataFrame(),
        "qc_work": pd.DataFrame(),
        "qc_map": {},
        "qc_idx": 0,
        "qc_step": "Question",
        "glossary": [],
        "vocab_query": "",
        "uploaded_name": None,
        "night": False,
    }.items():
        if k not in ss: ss[k] = v
    return ss

def minimal_work_copy(src: pd.DataFrame) -> pd.DataFrame:
    """Return a safe working copy (just a stub: returns src)."""
    return src.copy()
