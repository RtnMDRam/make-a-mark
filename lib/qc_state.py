import re
import streamlit as st

# ---------- CSS (once) ----------
def _cards_css_once():
    if st.session_state.get("_cards_css_done"):
        return
    st.session_state["_cards_css_done"] = True
    st.markdown(
        """
        <style>
          .ta-card,.en-card{border-radius:12px;padding:14px 16px;margin:12px 0}
          .ta-card{background:#EAF6E8}.en-card{background:#EAF0FF}
          .card-title{display:inline-block;font-weight:600;font-size:.95rem;
                      padding:3px 10px;border-radius:14px;margin-bottom:8px;background:#E2E8F0}
          .card-title.ta{background:#DCEFE1}.card-title.en{background:#DFE7F9}
          .row{margin:6px 0}.row b{color:#364152}.en-card{margin-bottom:8px}
        </style>
        """, unsafe_allow_html=True
    )

# ---------- helpers ----------
def _first_match(cols, *patterns):
    """Return first column name matching any pattern (case-insensitive), else None."""
    lc = {c.lower(): c for c in cols}
    for pat in patterns:
        rx = re.compile(pat, re.I)
        for c in cols:
            if rx.search(c): return c
    return None

def _pick(df, lang, kind):
    """
    Try many likely headers for a given (lang, kind).
    lang: 'ta' or 'en'
    kind: 'q','a','ex','opt_a','opt_b','opt_c','opt_d','opts_all'
    """
    cands = {
        ('ta','q'):   [r'^(ta_)?q(uestion)?', r'q_?ta', r'.*தமிழ.*\bq'],
        ('ta','a'):   [r'^(ta_)?a(ns(w|)er)?$', r'ans_?ta', r'.*தமிழ.*\bans'],
        ('ta','ex'):  [r'^(ta_)?ex(p(lanation)?)?$', r'exp_?ta', r'.*தமிழ.*\bexp'],
        ('ta','opt_a'):[r'^(ta_)?(opt_?)?a$', r'ta[_ ]?a[_ ]?opt'],
        ('ta','opt_b'):[r'^(ta_)?(opt_?)?b$', r'ta[_ ]?b[_ ]?opt'],
        ('ta','opt_c'):[r'^(ta_)?(opt_?)?c$', r'ta[_ ]?c[_ ]?opt'],
        ('ta','opt_d'):[r'^(ta_)?(opt_?)?d$', r'ta[_ ]?d[_ ]?opt'],
        ('ta','opts_all'):[r'^(ta_)?options?', r'opts?_?ta'],
        ('en','q'):   [r'^(en_)?q(uestion)?', r'q_?en', r'^question$'],
        ('en','a'):   [r'^(en_)?a(ns(w|)er)?$', r'ans_?en', r'^answer$'],
        ('en','ex'):  [r'^(en_)?ex(p(lanation)?)?$', r'exp_?en', r'^explanation$'],
        ('en','opt_a'):[r'^(en_)?(opt_?)?a$', r'en[_ ]?a[_ ]?opt'],
        ('en','opt_b'):[r'^(en_)?(opt_?)?b$', r'en[_ ]?b[_ ]?opt'],
        ('en','opt_c'):[r'^(en_)?(opt_?)?c$', r'en[_ ]?c[_ ]?opt'],
        ('en','opt_d'):[r'^(en_)?(opt_?)?d$', r'en[_ ]?d[_ ]?opt'],
        ('en','opts_all'):[r'^(en_)?options?', r'^options$'],
    }
    cols = list(df.columns)
    patts = cands.get((lang,kind), [])
    col = _first_match(cols, *patts) if patts else None
    return col

def _val(row, col):
    if not col: return ""
    v = row.get(col, "")
    return "" if (v is None) else str(v).strip()

def _parse_opts_string(s):
    """Split a single options string into 4 pieces, tolerant of formats."""
    if not s: return ["","","",""]
    txt = str(s)
    # unify separators
    txt = txt.replace("\n", " ").replace("\r", " ")
    # split by | or ; or , if present
    if "|" in txt: parts = [p.strip() for p in txt.split("|")]
    elif ";" in txt: parts = [p.strip() for p in txt.split(";")]
    elif "," in txt: parts = [p.strip() for p in txt.split(",")]
    else:
        # try numbered/listed like "1) A ... 2) B ..." or "A) ... B) ..."
        parts = re.split(r'\b(?:1\)|2\)|3\)|4\)|A\)|B\)|C\)|D\))', txt)
        parts = [p.strip() for p in parts if p.strip()]
    parts = (parts + ["","","",""])[:4]
    return parts

def _fmt_opts_ta(vals):  # A) … | B) … | C) … | D) …
    L = []
    lab = ["A","B","C","D"]
    for i,v in enumerate(vals): L.append(f"{lab[i]}) {v}" if v else "—")
    return " | ".join(L)

def _fmt_opts_en(vals):  # 1) … | 2) … | 3) … | 4) …
    L = []
    for i,v in enumerate(vals,1): L.append(f"{i}) {v}" if v else "—")
    return " | ".join(L)

# ---------- main renderer ----------
def render_reference_and_editor():
    _cards_css_once()

    df = st.session_state.get("qc_df")
    idx = st.session_state.get("qc_idx", 0)
    if df is None or len(df)==0: return
    row = df.iloc[idx]

    # ----- Tamil picks -----
    ta_q  = _val(row, _pick(df,'ta','q'))
    ta_a  = _val(row, _pick(df,'ta','a'))
    ta_ex = _val(row, _pick(df,'ta','ex'))
    taA   = _val(row, _pick(df,'ta','opt_a'))
    taB   = _val(row, _pick(df,'ta','opt_b'))
    taC   = _val(row, _pick(df,'ta','opt_c'))
    taD   = _val(row, _pick(df,'ta','opt_d'))
    if not any([taA,taB,taC,taD]):
        taAll = _val(row, _pick(df,'ta','opts_all'))
        taA,taB,taC,taD = _parse_opts_string(taAll)

    # ----- English picks -----
    en_q  = _val(row, _pick(df,'en','q'))
    en_a  = _val(row, _pick(df,'en','a'))
    en_ex = _val(row, _pick(df,'en','ex'))
    enA   = _val(row, _pick(df,'en','opt_a'))
    enB   = _val(row, _pick(df,'en','opt_b'))
    enC   = _val(row, _pick(df,'en','opt_c'))
    enD   = _val(row, _pick(df,'en','opt_d'))
    if not any([enA,enB,enC,enD]):
        enAll = _val(row, _pick(df,'en','opts_all'))
        enA,enB,enC,enD = _parse_opts_string(enAll)

    # ----- cards -----
    st.markdown(
        f"""
        <div class="ta-card">
          <span class="card-title ta">தமிழ் மூலப் பதிவு</span>
          <div class="row"><b>Q:</b> {ta_q or "—"}</div>
          <div class="row"><b>Options (A–D):</b> {_fmt_opts_ta([taA,taB,taC,taD])}</div>
          <div class="row"><b>Answer:</b> {ta_a or "—"}</div>
          <div class="row"><b>Explanation:</b> {ta_ex or "—"}</div>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class="en-card">
          <span class="card-title en">English Version</span>
          <div class="row"><b>Q:</b> {en_q or "—"}</div>
          <div class="row"><b>Options (A–D):</b> {_fmt_opts_en([enA,enB,enC,enD])}</div>
          <div class="row"><b>Answer:</b> {en_a or "—"}</div>
          <div class="row"><b>Explanation:</b> {en_ex or "—"}</div>
        </div>
        """, unsafe_allow_html=True
    )
