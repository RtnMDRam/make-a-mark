import streamlit as st

# --- 1) one-time CSS for reference cards (paste once in this file) ---
def _cards_css_once():
    if st.session_state.get("_cards_css_done"):
        return
    st.session_state["_cards_css_done"] = True
    st.markdown(
        """
        <style>
            /* card shells */
            .ta-card, .en-card{
                border-radius:12px;
                padding:14px 16px;
                margin:12px 0;
            }
            .ta-card{ background:#EAF6E8; }   /* light green */
            .en-card{ background:#EAF0FF; }   /* light blue */

            /* chip-like titles */
            .card-title{
                display:inline-block;
                font-weight:600;
                font-size:0.95rem;
                padding:3px 10px;
                border-radius:14px;
                margin-bottom:8px;
                background:#E2E8F0;           /* default chip bg */
            }
            .card-title.ta{ background:#DCEFE1; }  /* Tamil chip */
            .card-title.en{ background:#DFE7F9; }  /* English chip */

            /* label + content rows */
            .row{ margin:6px 0; }
            .row b{ color:#364152; }
            .thin{ margin-top:4px; }

            /* tighten bottom whitespace of the last card */
            .en-card{ margin-bottom:8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- 2) helpers to format the Options line exactly like your reference ---
def _format_opts_ta(opts):  # A) … | B) … | C) … | D) …
    parts = []
    labels = ["A", "B", "C", "D"]
    for i, v in enumerate(opts):
        parts.append(f"{labels[i]}) {v}" if (v and str(v).strip()) else "—")
    return " | ".join(parts)

def _format_opts_en(opts):  # 1) … | 2) … | 3) … | 4) …
    parts = []
    for i, v in enumerate(opts, start=1):
        parts.append(f"{i}) {v}" if (v and str(v).strip()) else "—")
    return " | ".join(parts)

# --- 3) main renderer (keeps your editor on top; shows Tamil & English cards) ---
def render_reference_and_editor():
    """
    Expects in session (already set by your Load handler):
      st.session_state.qc_df       : pandas.DataFrame for the current file
      st.session_state.qc_idx      : int, current row index
    Also expects your editor widgets to be rendered before or after as you prefer.
    """
    _cards_css_once()

    df = st.session_state.get("qc_df")
    idx = st.session_state.get("qc_idx", 0)
    if df is None or len(df) == 0:
        return

    row = df.iloc[idx]

    # Pull Tamil/English values using your column keys (adjust names if different)
    ta_q   = row.get("ta_q", "") or row.get("q_ta", "") or ""
    ta_a   = row.get("ta_a", "") or row.get("ans_ta", "") or ""
    ta_ex  = row.get("ta_ex", "") or row.get("exp_ta", "") or ""
    taA    = row.get("ta_opt_a", "") or row.get("ta_a_opt", "") or row.get("ta_A", "")
    taB    = row.get("ta_opt_b", "") or row.get("ta_b_opt", "") or row.get("ta_B", "")
    taC    = row.get("ta_opt_c", "") or row.get("ta_c_opt", "") or row.get("ta_C", "")
    taD    = row.get("ta_opt_d", "") or row.get("ta_d_opt", "") or row.get("ta_D", "")

    en_q   = row.get("en_q", "") or row.get("q_en", "") or ""
    en_a   = row.get("en_a", "") or row.get("ans_en", "") or ""
    en_ex  = row.get("en_ex", "") or row.get("exp_en", "") or ""
    enA    = row.get("en_opt_a", "") or row.get("en_a_opt", "") or row.get("en_A", "")
    enB    = row.get("en_opt_b", "") or row.get("en_b_opt", "") or row.get("en_B", "")
    enC    = row.get("en_opt_c", "") or row.get("en_c_opt", "") or row.get("en_C", "")
    enD    = row.get("en_opt_d", "") or row.get("en_d_opt", "") or row.get("en_D", "")

    # Build Options line strings
    ta_opts_line = _format_opts_ta([taA, taB, taC, taD])
    en_opts_line = _format_opts_en([enA, enB, enC, enD])

    # --- Tamil card (title only in Tamil) ---
    st.markdown(
        f"""
        <div class="ta-card">
          <span class="card-title ta">தமிழ் மூலப் பதிவு</span>
          <div class="row"><b>Q:</b> {ta_q or "—"}</div>
          <div class="row"><b>Options (A–D):</b> {ta_opts_line}</div>
          <div class="row"><b>Answer:</b> {ta_a or "—"}</div>
          <div class="row"><b>Explanation:</b> {ta_ex or "—"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- English card (title only in English) ---
    st.markdown(
        f"""
        <div class="en-card">
          <span class="card-title en">English Version</span>
          <div class="row"><b>Q:</b> {en_q or "—"}</div>
          <div class="row"><b>Options (A–D):</b> {en_opts_line}</div>
          <div class="row"><b>Answer:</b> {en_a or "—"}</div>
          <div class="row"><b>Explanation:</b> {en_ex or "—"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
