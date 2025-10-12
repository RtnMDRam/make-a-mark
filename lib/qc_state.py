# lib/qc_state.py
import streamlit as st
import pandas as pd

# ----------------- small helpers -----------------
def _val(x):
    """Return a clean display value; use em dash for empty."""
    if x is None:
        return "—"
    try:
        if pd.isna(x):
            return "—"
    except Exception:
        pass
    s = str(x).strip()
    return s if s else "—"

def _options_row(prefix: str, row: dict) -> str:
    """
    Build 'A | B | C | D' for Tamil/English panels.
    Accepts either {prefix}A,{prefix}B,{prefix}C,{prefix}D
    or {prefix}opt_a...{prefix}opt_d. Missing -> '—'
    """
    tries = [
        f"{prefix}A", f"{prefix}B", f"{prefix}C", f"{prefix}D",
        f"{prefix}opt_a", f"{prefix}opt_b", f"{prefix}opt_c", f"{prefix}opt_d",
    ]
    # keep the first occurrence of a,b,c,d in order
    picked, seen = [], set()
    for k in tries:
        if k in row:
            base = k.split("_")[-1].lower()
            if base in ("a", "b", "c", "d") and base not in seen:
                picked.append(k)
                seen.add(base)
                if len(picked) == 4:
                    break
    while len(picked) < 4:
        picked.append(None)
    vals = [_val(row.get(k)) if k else "—" for k in picked]
    return " | ".join(vals)

def _css_once_reference():
    st.markdown(
        """
        <style>
        .ref-card{border:1px solid rgba(0,0,0,.08); border-radius:10px; padding:14px 16px; margin:10px 0;}
        .ref-ta{background:#EFF8EE;}
        .ref-en{background:#EAF2FD;}
        .ref-title{font-weight:700; font-size:18px; margin:2px 0 8px 0;}
        .field-label,.minor-label{font-size:13px; font-weight:600; margin:0 0 6px 0;}
        .field-label{color:#2f4f3a;}
        .minor-label{color:#3a3a3a;}
        .boxed{background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:8px; padding:10px 12px;}
        .tight{margin-top:6px; margin-bottom:8px;}
        .gap12{height:12px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ----------------- main renderer -----------------
def render_reference_and_editor():
    """
    Renders: SME Edit Console (top) → Tamil Original (middle) → English Version (bottom).
    Needs:
      st.session_state.qc_df  : pandas.DataFrame
      st.session_state.qc_idx : int
    """
    _css_once_reference()

    df = st.session_state.get("qc_df")
    idx = st.session_state.get("qc_idx", 0)
    if not isinstance(df, pd.DataFrame) or df.empty or idx not in df.index:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")
        return

    row = df.loc[idx].to_dict()

    # -------- SME Edit Console (TOP) --------
    st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

    q_col, ans_col = st.columns([3, 2], gap="small")
    with q_col:
        st.text_area(
            "கேள்வி :", _val(row.get("ta_q") or row.get("q_ta") or row.get("q_tamil")),
            key=f"ta_q_{idx}", height=84
        )
    with ans_col:
        st.text_input(
            "பதில் / Answer", _val(row.get("ta_answer") or row.get("answer_ta") or row.get("ans_tamil")),
            key=f"ta_ans_{idx}"
        )

    left, right = st.columns(2, gap="small")
    with left:
        c1, c2 = st.columns(2, gap="small")
        c1.text_input("A", _val(row.get("ta_A") or row.get("ta_opt_a")), key=f"ta_A_{idx}")
        c2.text_input("B", _val(row.get("ta_B") or row.get("ta_opt_b")), key=f"ta_B_{idx}")
    with right:
        c3, c4 = st.columns(2, gap="small")
        c3.text_input("C", _val(row.get("ta_C") or row.get("ta_opt_c")), key=f"ta_C_{idx}")
        c4.text_input("D", _val(row.get("ta_D") or row.get("ta_opt_d")), key=f"ta_D_{idx}")

    gcol, ecol = st.columns([2,3], gap="small")
    with gcol:
        st.text_input("சொல் அகராதி / Glossary (Type the word)", "", key=f"gloss_{idx}")
    with ecol:
        st.text_area("விளக்கங்கள் :", _val(row.get("ta_explain") or row.get("explain_ta")),
                     key=f"ta_exp_{idx}", height=84)

    st.markdown("<div class='gap12'></div>", unsafe_allow_html=True)

    # -------- Tamil Original (MIDDLE) --------
    st.markdown("<div class='ref-card ref-ta'>", unsafe_allow_html=True)
    st.markdown("<div class='ref-title'>Tamil Original / தமிழ் மூலப் பதிப்பு</div>", unsafe_allow_html=True)

    q_ta   = _val(row.get("ta_q") or row.get("q_ta") or row.get("q_tamil"))
    opts_t = _options_row("ta_", row)
    ans_ta = _val(row.get("ta_answer") or row.get("answer_ta") or row.get("ans_tamil"))
    exp_ta = _val(row.get("ta_explain") or row.get("explain_ta"))

    st.markdown("<div class='field-label'>Q:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{q_ta}</div>", unsafe_allow_html=True)

    st.markdown("<div class='field-label'>Options (A–D):</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{opts_t}</div>", unsafe_allow_html=True)

    st.markdown("<div class='field-label'>Answer:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{ans_ta}</div>", unsafe_allow_html=True)

    st.markdown("<div class='field-label'>Explanation:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed'>{exp_ta}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='gap12'></div>", unsafe_allow_html=True)

    # -------- English Version (BOTTOM) --------
    st.markdown("<div class='ref-card ref-en'>", unsafe_allow_html=True)
    st.markdown("<div class='ref-title'>English Version / ஆங்கிலம்</div>", unsafe_allow_html=True)

    q_en   = _val(row.get("en_q") or row.get("q_en") or row.get("question"))
    opts_e = _options_row("en_", row)
    ans_en = _val(row.get("en_answer") or row.get("answer_en") or row.get("answer"))
    exp_en = _val(row.get("en_explain") or row.get("explain_en") or row.get("explanation"))

    st.markdown("<div class='minor-label'>Q:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{q_en}</div>", unsafe_allow_html=True)

    st.markdown("<div class='minor-label'>Options (A–D):</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{opts_e}</div>", unsafe_allow_html=True)

    st.markdown("<div class='minor-label'>Answer:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed tight'>{ans_en}</div>", unsafe_allow_html=True)

    st.markdown("<div class='minor-label'>Explanation:</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='boxed'>{exp_en}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
