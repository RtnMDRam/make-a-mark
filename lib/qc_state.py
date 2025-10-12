# lib/qc_state.py
import streamlit as st
import pandas as pd

# ---------- small helpers ----------
def _col(df: pd.DataFrame, name_choices):
    """Return the first matching column value for the current row index."""
    idx = st.session_state.get("qc_idx", 0)
    for n in name_choices:
        if n in df.columns:
            val = df.iloc[idx][n]
            # Normalize NaN / None to empty string
            return "" if pd.isna(val) else str(val)
    return ""

def _fmt_opts(*opts):
    """Join non-empty options as 1) … | 2) … | 3) … | 4) …"""
    clean = [o for o in opts if o and o.strip()]
    if not clean:
        return "—"
    numd = [f"{i}) {txt.strip()}" for i, txt in enumerate(clean, 1)]
    return " | ".join(numd)

def _card(title: str, q: str, a: str, b: str, c: str, d: str, ans: str, expl: str, pale_class: str):
    """Draw one non-editable reference card."""
    st.markdown(
        f"""
        <div class="{pale_class} en-card">
          <p><b>Question / கேள்வி:</b> {q or "—"}</p>
          <p><b>Options / விருப்பங்கள் (A–D):</b> {_fmt_opts(a,b,c,d)}</p>
          <p><b>Answer / பதில்:</b> {ans or "—"}</p>
          <p><b>Explanation / விளக்கம்:</b> {expl or "—"}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- light CSS for the two cards ----------
def _css_ref_only():
    st.markdown(
        """
        <style>
          .en-card{
            padding: 14px 18px; border-radius: 12px; 
            border: 1px solid rgba(0,0,0,.06); margin: 0 0 16px 0;
          }
          .pale-green{ background: #eef8ef;}
          .pale-blue{  background: #eef3ff;}
          .en-card p{ margin: 4px 0 8px 0; line-height: 1.45; }
          .en-card b{ font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------- PUBLIC: call this to show just the two reference blocks ----------
def render_reference_only():
    """
    Renders *non-editable* Tamil & English reference blocks with bilingual labels.
    Expects st.session_state.qc_df (pandas.DataFrame) and st.session_state.qc_idx (int).
    """
    df = st.session_state.get("qc_df", None)
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return

    _css_ref_only()

    # ---- Tamil fields (use tolerant column names) ----
    ta_q   = _col(df, ["ta_q", "ta_question", "question_ta"])
    ta_a   = _col(df, ["ta_opt_a", "ta_a", "ta_optA", "ta_A"])
    ta_b   = _col(df, ["ta_opt_b", "ta_b", "ta_optB", "ta_B"])
    ta_c   = _col(df, ["ta_opt_c", "ta_c", "ta_optC", "ta_C"])
    ta_d   = _col(df, ["ta_opt_d", "ta_d", "ta_optD", "ta_D"])
    ta_ans = _col(df, ["ta_ans", "ta_answer", "answer_ta"])
    ta_ex  = _col(df, ["ta_ex", "ta_explanation", "explain_ta"])

    # ---- English fields ----
    en_q   = _col(df, ["en_q", "question", "en_question"])
    en_a   = _col(df, ["en_opt_a", "opt_a", "en_a", "A"])
    en_b   = _col(df, ["en_opt_b", "opt_b", "en_b", "B"])
    en_c   = _col(df, ["en_opt_c", "opt_c", "en_c", "C"])
    en_d   = _col(df, ["en_opt_d", "opt_d", "en_d", "D"])
    en_ans = _col(df, ["en_ans", "answer", "en_answer"])
    en_ex  = _col(df, ["en_ex", "explanation", "en_explanation"])

    # ---- Render (Tamil first, English next) ----
    st.markdown('<div class="pale-green en-card" style="margin-bottom:0"><b style="opacity:.7; padding:4px 10px; background:#e2f1e4; border-radius:12px;">தமிழ் மூலப் பதிப்பு</b></div>', unsafe_allow_html=True)
    _card("ta", ta_q, ta_a, ta_b, ta_c, ta_d, ta_ans, ta_ex, "pale-green")

    st.markdown('<div class="pale-blue en-card" style="margin-top:8px; margin-bottom:0"><b style="opacity:.7; padding:4px 10px; background:#e7edff; border-radius:12px;">English Version</b></div>', unsafe_allow_html=True)
    _card("en", en_q, en_a, en_b, en_c, en_d, en_ans, en_ex, "pale-blue")
