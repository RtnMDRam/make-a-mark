import unicodedata
import re

# --- replace the old helpers: _clean, _opts_as_line stay the same ---

def _norm(s: str) -> str:
    """Normalize a column name: strip, lowercase, collapse spaces & nbsp, drop punctuation."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("\u00A0", " ").replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    # remove punctuation & separators so 'question_options' → 'questionoptions'
    s = re.sub(r"[^0-9a-zA-Z\u0B80-\u0BFF]", "", s)  # keep Tamil block too
    return s

def _cols_detect(df):
    """
    Robust auto-detect.
    English accepts: question, q
                     questionoptions / options / option
                     answers / answer / ans
                     explanation / explain / exp
    Tamil accepts startswith of: கேள்வி, விருப்பங்கள், பதில், விளக்கம்
    Works even with spaces, nbsp, punctuation, case differences.
    """
    # Build normalized lookup
    norm_to_actual = {}
    for c in df.columns:
        norm_to_actual[_norm(c)] = c

    # helpers
    def pick(norm_candidates):
        for cand in norm_candidates:
            if cand in norm_to_actual:
                return norm_to_actual[cand]
        return None

    # English
    en_q = pick(["question","q","enquestion","enq"])
    en_o = pick(["questionoptions","options","option","enoptions","enoption"])
    en_a = pick(["answers","answer","ans","enanswers","enanswer","enans"])
    en_e = pick(["explanation","explain","exp","enexplanation","enexplain","enexp"])

    # Tamil – allow fuzzy “starts with” on real column names (not normalized),
    # but try normalized too in case punctuation/nbsp exist.
    def pick_ta(prefix_tamil):
        # try exact/startswith on actual columns
        for c in df.columns:
            s = str(c).strip()
            if s.startswith(prefix_tamil):
                return c
        # fallback normalized
        pref_n = _norm(prefix_tamil)
        for c in df.columns:
            if _norm(c).startswith(pref_n):
                return c
        return None

    ta_q = pick_ta("கேள்வி")
    ta_o = pick_ta("விருப்பங்கள்")
    ta_a = pick_ta("பதில்")
    ta_e = pick_ta("விளக்கம்")

    return dict(en=dict(q=en_q, o=en_o, a=en_a, e=en_e),
                ta=dict(q=ta_q, o=ta_o, a=ta_a, e=ta_e))

def render_boxes_with_content():
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    df = st.session_state.get("qc_df")
    idx = int(st.session_state.get("qc_idx", 0))

    st.markdown(
        """
        <div class="stack">
          <div class="card ed-card"><h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4></div>
          <div class="card ta-card"><h4>தமிழ் மூலப் பதிப்பு</h4><div id="ta-body"></div></div>
          <div class="card en-card"><h4>English Version</h4><div id="en-body"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.warning("No data loaded yet. Upload a CSV/XLSX and press **Load**.")
        return
    if not (0 <= idx < len(df)):
        st.error(f"Row index {idx} is out of range (0–{len(df)-1}).")
        return

    cols = _cols_detect(df)
    row = df.iloc[idx]

    # ----- English first (render even if Tamil missing) -----
    en = cols["en"]
    en_html = ""
    if any(en.values()):
        en_q = _clean(row.get(en["q"])) if en["q"] else "—"
        en_o = _opts_as_line(row.get(en["o"])) if en["o"] else "—"
        en_a = _clean(row.get(en["a"])) if en["a"] else "—"
        en_e = _clean(row.get(en["e"])) if en["e"] else "—"
        en_html = (
            _line("Q :", en_q) +
            _line("Options (A–D) :", en_o) +
            _line("Answer :", en_a) +
            _line("Explanation :", en_e)
        )

    if en_html:
        st.markdown(f"""<script>
            const e=document.getElementById('en-body'); if(e) e.innerHTML = `{en_html}`;
        </script>""", unsafe_allow_html=True)

    # ----- Tamil (only if we find the columns; otherwise silently skip) -----
    ta = cols["ta"]
    if any(ta.values()):
        ta_q = _clean(row.get(ta["q"])) if ta["q"] else "—"
        ta_o = _opts_as_line(row.get(ta["o"])) if ta["o"] else "—"
        ta_a = _clean(row.get(ta["a"])) if ta["a"] else "—"
        ta_e = _clean(row.get(ta["e"])) if ta["e"] else "—"
        ta_html = (
            _line("கேள்வி :", ta_q) +
            _line("விருப்பங்கள் (A–D) :", ta_o) +
            _line("பதில் :", ta_a) +
            _line("விளக்கம் :", ta_e)
        )
        st.markdown(f"""<script>
            const t=document.getElementById('ta-body'); if(t) t.innerHTML = `{ta_html}`;
        </script>""", unsafe_allow_html=True)
