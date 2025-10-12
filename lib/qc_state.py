# lib/qc_state.py
# ——————————————————————————————————————————
# Renders the NON-editable reference cards (Tamil on top, English below)
# using whatever column names your CSV/XLSX provides.
# Layout/styling kept minimal so we do not disturb your current look.

from __future__ import annotations
import re
import html
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


# ---------- small CSS that matches your current cards ----------
def _css_once():
    if st.session_state.get("_qc_cards_css_done"):
        return
    st.session_state["_qc_cards_css_done"] = True
    st.markdown(
        """
<style>
/* keep the spacing & look you already have */
.qc-card {
  border-radius: 10px;
  padding: 16px 18px;
  margin: 0 0 18px 0;
}
.qc-ta { background: #eaf6e9; }     /* green (Tamil)  */
.qc-en { background: #e9f0ff; }     /* blue  (English) */

.qc-badge {
  display:inline-block;
  font-size: 13px; line-height: 1;
  padding: 6px 10px; border-radius: 14px;
  background: rgba(0,0,0,.06); color:#222;
  margin-bottom: 10px;
}
.qc-row  { margin: 6px 0 10px 0; }
.qc-lbl  { font-weight: 700; }
.qc-dash { color:#666; }
</style>
        """,
        unsafe_allow_html=True,
    )


# ---------- helpers ----------
def _first_match(colnames: List[str], candidates: List[str]) -> Optional[str]:
    """Return the first column name that exists in df among candidates."""
    # allow case-insensitive & trimmed comparison
    lc = {c.strip().lower(): c for c in colnames}
    for cand in candidates:
        key = cand.strip().lower()
        if key in lc:
            return lc[key]
    return None


def _get(df: pd.DataFrame, row: int, candidates: List[str]) -> str:
    name = _first_match(list(df.columns), candidates)
    if not name:
        return ""
    val = df.at[row, name]
    if pd.isna(val):
        return ""
    # flatten HTML-ish or Excel-rich text
    s = str(val)
    s = html.unescape(s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?(p|div|span|strong|b|em|i)[^>]*>", "", s, flags=re.I)
    s = s.replace("\r", "").replace("\n", " ").strip()
    return s


def _format_options(raw: str) -> str:
    """
    Try to normalize options to: A | B | C | D
    Accepts:
      - 'A) ... | B) ... | C) ... | D) ...'
      - '1) ... | 2) ... | 3) ... | 4) ...'
      - comma/pipe/semicolon separated
      - JSON-like '["A","B","C","D"]'
    """
    if not raw:
        return "— | — | — | —"

    s = raw.strip()

    # JSON-like
    if s.startswith("[") and s.endswith("]"):
        parts = [x.strip(" '\"\t") for x in s.strip("[]").split(",")]
        parts = [p for p in parts if p]
        while len(parts) < 4:
            parts.append("—")
        return " | ".join(parts[:4])

    # Split by labeled A)/B)/C)/D) or 1)/2)/3)/4)
    # Make sure we keep content after each marker
    m = re.split(r"\b(?:A\)|B\)|C\)|D\)|1\)|2\)|3\)|4\))", s)
    if len(m) > 1:
        # re.split keeps separators out; re-find all pieces by pattern
        items = re.findall(
            r"(?:A\)|1\))\s*(.*?)(?=(?:B\)|2\))|$)|"
            r"(?:B\)|2\))\s*(.*?)(?=(?:C\)|3\))|$)|"
            r"(?:C\)|3\))\s*(.*?)(?=(?:D\)|4\))|$)|"
            r"(?:D\)|4\))\s*(.*)$",
            s
        )
        flat: List[str] = []
        for tup in items:
            for piece in tup:
                if piece is not None and piece != "":
                    flat.append(piece.strip())
        if flat:
            while len(flat) < 4:
                flat.append("—")
            return " | ".join(flat[:4])

    # fallback split by common separators
    parts = re.split(r"\s*\|\s*|\s*[,;/]\s*", s)
    parts = [p for p in [p.strip() for p in parts] if p]
    while len(parts) < 4:
        parts.append("—")
    return " | ".join(parts[:4])


def _render_card(title_badge: str, labels: Dict[str, str], data: Dict[str, str], css_class: str):
    st.markdown(
        f"""
<div class="qc-card {css_class}">
  <div class="qc-badge">{title_badge}</div>

  <div class="qc-row"><span class="qc-lbl">{labels['q']}</span> {data['q'] or '—'}</div>
  <div class="qc-row"><span class="qc-lbl">{labels['opts']}</span> { _format_options(data['opts']) }</div>
  <div class="qc-row"><span class="qc-lbl">{labels['ans']}</span> {data['ans'] or '—'}</div>
  <div class="qc-row"><span class="qc-lbl">{labels['exp']}</span> {data['exp'] or '—'}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ---------- main public renderer (called by your page) ----------
def render_reference_and_editor():
    """
    We only render the two reference cards here (no editor now).
    Uses st.session_state.qc_df (DataFrame) and st.session_state.qc_idx (int).
    """
    _css_once()

    df: Optional[pd.DataFrame] = st.session_state.get("qc_df")
    if df is None or df.empty:
        return

    idx: int = int(st.session_state.get("qc_idx", 0))
    idx = max(0, min(idx, len(df) - 1))

    cols = list(df.columns)

    # Column candidates (keep both English & Tamil headers)
    EN = {
        "q":    ["question", "en_q", "english", "english_question", "q", "question_text"],
        "opts": ["questionOptions", "options", "en_options", "english_options"],
        "ans":  ["answers", "answer", "en_answer", "english_answer"],
        "exp":  ["explanation", "explanations", "en_explanation", "english_explanation"],
    }
    TA = {
        "q":    ["கேள்வி", "ta_q", "tamil", "tamil_question"],
        "opts": ["விருப்பங்கள் (A–D)", "விருப்பங்கள் (A-D)", "விருப்பங்கள்", "தெரிவுகள்", "ta_options"],
        "ans":  ["பதில்", "ta_answer"],
        "exp":  ["விளக்கம்", "ta_explanation"],
    }

    # Read Tamil & English pieces from the same row
    ta_data = {
        "q":    _get(df, idx, TA["q"]),
        "opts": _get(df, idx, TA["opts"]),
        "ans":  _get(df, idx, TA["ans"]),
        "exp":  _get(df, idx, TA["exp"]),
    }
    en_data = {
        "q":    _get(df, idx, EN["q"]),
        "opts": _get(df, idx, EN["opts"]),
        "ans":  _get(df, idx, EN["ans"]),
        "exp":  _get(df, idx, EN["exp"]),
    }

    # Labels (Tamil label set for Tamil card; English for English card)
    ta_labels = {
        "q":   "கேள்வி: ",
        "opts":"விருப்பங்கள் (A–D): ",
        "ans": "பதில்: ",
        "exp": "விளக்கம்: ",
    }
    en_labels = {
        "q":   "Q: ",
        "opts":"Options (A–D): ",
        "ans": "Answer: ",
        "exp": "Explanation: ",
    }

    # Always render Tamil card first, English card second (your required order)
    _render_card("தமிழ் மூலப் பதிப்பு", ta_labels, ta_data, "qc-ta")
    _render_card("English Version",   en_labels, en_data, "qc-en")
