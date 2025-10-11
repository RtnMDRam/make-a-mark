# lib/qc_state.py
import re
import pandas as pd

def _digits_only(s, n=None):
    v = re.sub(r"\D", "", str(s or ""))
    return v[:n] if n else v

def auto_guess_map(df: pd.DataFrame) -> dict:
    """Best-effort column guessing based on common header patterns."""
    def guess(one_of):
        for cand in one_of:
            for c in df.columns:
                if cand.lower() in str(c).lower():
                    return c
        return None
    return {
        "ID":     guess(["id","qid","serial"]),
        "Q_EN":   guess(["question (english)","question_en","question english","q_en","question"]),
        "OPT_EN": guess(["options (english)","options_en","opt_en","options"]),
        "ANS_EN": guess(["answer (english)","ans_en","answer"]),
        "EXP_EN": guess(["explanation (english)","exp_en","explanation"]),
        "Q_TA":   guess(["question (tamil)","question_tamil","q_ta","தமிழ் கேள்வி"]),
        "OPT_TA": guess(["options (tamil)","options_ta","opt_ta","விருப்பங்கள்"]),
        "ANS_TA": guess(["answer (tamil)","ans_ta","பதில்"]),
        "EXP_TA": guess(["explanation (tamil)","exp_ta","விளக்கம்"]),
    }

def ensure_work(df_src: pd.DataFrame, m: dict) -> pd.DataFrame:
    """Create working copy with QC_* columns (starting from TA originals)."""
    work = pd.DataFrame(index=df_src.index)
    for k in ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]:
        col = m.get(k)
        work[k] = df_src[col].astype(str).fillna("") if col in df_src.columns else ""
    work["QC_Q_TA"]   = work["Q_TA"]
    work["QC_OPT_TA"] = work["OPT_TA"]
    work["QC_ANS_TA"] = work["ANS_TA"]
    work["QC_EXP_TA"] = work["EXP_TA"]
    return work.reset_index(drop=True)

def step_columns(step: str) -> dict:
    """Return the appropriate EN/TA/QC columns for the current step."""
    step = (step or "Question").lower()
    if step == "question":
        return {"EN":"Q_EN","TA":"Q_TA","QC":"QC_Q_TA"}
    if step == "options":
        return {"EN":"OPT_EN","TA":"OPT_TA","QC":"QC_OPT_TA"}
    if step == "answer":
        return {"EN":"ANS_EN","TA":"ANS_TA","QC":"QC_ANS_TA"}
    return {"EN":"EXP_EN","TA":"EXP_TA","QC":"QC_EXP_TA"}
