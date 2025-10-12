# lib/qc_state.py
import re
import streamlit as st

# ---------- COMPACT LAYOUT CSS ----------
_LAYOUT_CSS = """
<style>
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:8px; padding-bottom:8px;}

.stack{display:grid; grid-template-rows:auto auto auto; row-gap:0;}
.card{
  margin:0;
  padding:4px 10px 8px 10px;        /* tight top title */
  border:2px solid #c0c7d0;
  border-radius:8px;
  background:#fff;
}

/* Box order / colors (easy to change later) */
.ed-card{min-height:40vh; border-color:#1f4fbf;}   /* top (SME) */
.ta-card{min-height:25vh; border-color:#199c4b;}   /* middle (Tamil) */
.en-card{min-height:25vh; border-color:#316dca;}   /* bottom (English) */

/* Titles smaller & close to top */
.card h4{
  font-size:12px !important;
  font-weight:600;
  margin:0;
  padding-top:2px;
  padding-bottom:6px;
}

/* Body text smaller */
.card p, .card div, .card span {
  font-size:12px !important;
  line-height:1.3em;
  margin:0;
  padding:0;
}

/* Label + value rows */
.pair{display:grid; grid-template-columns:auto 1fr; column-gap:8px; row-gap:6px;}
.label{font-weight:600; opacity:.9}
.sep{opacity:.85}
hr.thin{border:none; border-top:1px solid rgba(0,0,0,.08); margin:6px 0 0 0;}
</style>
"""

# ---------- helpers ----------
TAG = re.compile(r"<[^>]+>")  # very light HTML stripper

def _dash_if_empty(x:str) -> str:
    x = (x or "").strip()
    return "—" if not x else x

def _clean(x:str) -> str:
    if x is None: return "—"
    x = TAG.sub("", str(x))                # strip simple tags
    x = x.replace("&nbsp;", " ").replace("\u00A0", " ")
    x = re.sub(r"\s+\|\s+", " | ", x)      # tidy pipes
    x = re.sub(r"\s+", " ", x).strip()
    return _dash_if_empty(x)

def _opts_as_line(x:str) -> str:
    """Keep A–D visually compact like:  — | — | — | — """
    x = _clean(x)
    # If options already look like "1) foo | 2) bar ..." keep as is
    # Else, try to join comma/pipe separated bits with visual pipes.
    if " | " in x or ")" in x:
        return x
    parts = [p.strip() for p in re.split(r"[,\|/;]", x) if p.strip()]
    return " | ".join(parts) if parts else x

def _line(label, value):
    return f'<div class="pair"><div class="label">{label}</div><div class="sep">{value}</div></div>'

def _cols_detect(df):
    """
    Auto-detect column names.
    English: question / questionOptions / answers / explanation
    Tamil  : கேள்வி / விருப்பங்கள் / பதில் / விளக்கம் (allow variants)
    """
    cols = {c.lower(): c for c in df.columns}

    en_q  = cols.get("question")
    en_o  = cols.get("questionoptions") or cols.get("options") or cols.get("option")
    en_a  = cols.get("answers") or cols.get("answer")
    en_e  = cols.get("explanation")

    # Tamil by exact/starts-with to cover slight differences
    def pick_any(names):
        for n in df.columns:
            for want in names:
                if str(n).strip().startswith(want):
                    return n
        return None

    ta_q = pick_any(["கேள்வி"])
    ta_o = pick_any(["விருப்பங்கள்"])
    ta_a = pick_any(["பதில்"])
    ta_e = pick_any(["விளக்கம்"])

    return dict(en=dict(q=en_q, o=en_o, a=en_a, e=en_e),
                ta=dict(q=ta_q, o=ta_o, a=ta_a, e=ta_e))

def _missing_columns(cols):
    miss = []
    for lang, m in cols.items():
        for k, v in m.items():
            if v is None:
                miss.append(f"{lang}.{k}")
    return miss

# ---------- renderers ----------
def render_boxes_with_content():
    """
    Shows:
      TOP   = empty SME box (editable area to wire later)
      MIDDLE= Tamil non-editable reference (if columns exist)
      BOTTOM= English non-editable reference (if columns exist)
    Reads: st.session_state.qc_df  (DataFrame) and st.session_state.qc_idx (int)
    """
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    df = st.session_state.get("qc_df")
    idx = int(st.session_state.get("qc_idx", 0))

    # Skeleton boxes
    st.markdown(
        """
        <div class="stack">
          <div class="card ed-card"><h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>
          </div>
          <div class="card ta-card"><h4>தமிழ் மூலப் பதிப்பு</h4>
            <div id="ta-body"></div>
          </div>
          <div class="card en-card"><h4>English Version</h4>
            <div id="en-body"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.warning("No data loaded yet. Upload a CSV/XLSX and press **Load**.")
        return

    if idx < 0 or idx >= len(df):
        st.error(f"Row index {idx} is out of range (0–{len(df)-1}).")
        return

    cols = _cols_detect(df)
    missing = _missing_columns(cols)
    if missing:
        st.info("Some expected columns were not found: " + ", ".join(missing))

    row = df.iloc[idx]

    # Build Tamil block (only if columns exist)
    ta = cols["ta"]
    ta_html = ""
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

    # Build English block (only if columns exist)
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

    # Inject into the two boxes
    if ta_html:
        st.markdown(f"""<script>
            const t=document.getElementById('ta-body'); if(t) t.innerHTML = `{ta_html}`;
        </script>""", unsafe_allow_html=True)

    if en_html:
        st.markdown(f"""<script>
            const e=document.getElementById('en-body'); if(e) e.innerHTML = `{en_html}`;
        </script>""", unsafe_allow_html=True)
