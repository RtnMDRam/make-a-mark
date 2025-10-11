# lib/qc_state.py
import pandas as pd

REQUIRED_KEYS = ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]

def auto_guess_map(df: pd.DataFrame) -> dict:
    """Best-effort guess of important columns from source headers."""
    def guess(names):
        for cand in names:
            for col in df.columns:
                if cand in str(col).lower():
                    return col
        return None
    return {
        "ID":     guess(["id","qid","serial"]),
        "Q_EN":   guess(["question (english)", "question_en", "question english", "q_en"]),
        "OPT_EN": guess(["options (english)", "options_en", "option (english)", "opt_en"]),
        "ANS_EN": guess(["answer (english)", "ans_en", "answer en"]),
        "EXP_EN": guess(["explanation (english)", "exp_en", "explanation en"]),
        "Q_TA":   guess(["question (tamil)", "question_tamil", "q_ta"]),
        "OPT_TA": guess(["options (tamil)", "options_ta", "opt_ta"]),
        "ANS_TA": guess(["answer (tamil)", "ans_ta", "answer ta"]),
        "EXP_TA": guess(["explanation (tamil)", "exp_ta", "explanation ta"]),
    }

def ensure_work(df_src: pd.DataFrame, m: dict) -> pd.DataFrame:
    """Create a working df with QC columns seeded from TA originals; index preserved."""
    work = pd.DataFrame(index=df_src.index)
    # copy passthrough for convenience
    for k in ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]:
        col = m.get(k)
        work[k] = df_src[col].astype(str).fillna("") if col in df_src.columns else ""
    # QC columns start with TA originals
    work["QC_Q_TA"]   = work["Q_TA"]
    work["QC_OPT_TA"] = work["OPT_TA"]
    work["QC_ANS_TA"] = work["ANS_TA"]
    work["QC_EXP_TA"] = work["EXP_TA"]
    return work.reset_index(drop=True)

def step_columns(step: str) -> dict:
    """Return the columns key mapping for the requested step."""
    base = {
        "Question":     {"EN":"Q_EN",   "TA":"Q_TA",   "QC":"QC_Q_TA"},
        "Options":      {"EN":"OPT_EN", "TA":"OPT_TA", "QC":"QC_OPT_TA"},
        "Answer":       {"EN":"ANS_EN", "TA":"ANS_TA", "QC":"QC_ANS_TA"},
        "Explanation":  {"EN":"EXP_EN", "TA":"EXP_TA", "QC":"QC_EXP_TA"},
    }
    return base.get(step, base["Question"])
