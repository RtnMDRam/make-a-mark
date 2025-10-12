# lib/header_bar.py
from datetime import datetime, date
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import streamlit as st

_TA_MONTHS = [
    ("சித்திரை", (4, 14)),
    ("வைகாசி",  (5, 15)),
    ("ஆனி",     (6, 15)),
    ("ஆடி",     (7, 16)),
    ("ஆவணி",    (8, 17)),
    ("புரட்டாசி", (9, 17)),
    ("ஐப்பசி",   (10, 17)),
    ("கார்த்திகை",(11,16)),
    ("மார்கழி",  (12,16)),
    ("தை",      (1, 14)),
    ("மாசி",     (2, 13)),
    ("பங்குனி",  (3, 14)),
]

def _tamil_month_info(gdt: date):
    starts = []
    for name, (m, d) in _TA_MONTHS:
        for yr in (gdt.year-1, gdt.year, gdt.year+1):
            starts.append((date(yr, m, d), name))
    starts = sorted(set(starts), key=lambda x: x[0])
    prior = max([sd for sd in starts if sd[0] <= gdt], key=lambda x: x[0])
    return (gdt - prior[0]).days + 1, prior[1]

def render_header(top_height_vh: int = 5):
    now = datetime.now(ZoneInfo("Asia/Kolkata") if ZoneInfo else None)
    day_ta, ta_month = _tamil_month_info(now.date())
    left_text = f"{day_ta} {ta_month} {now.year} {now.strftime('%b %d')}"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600&display=swap" rel="stylesheet">
    <style>
      :root {{ --header-h: {top_height_vh}dvh; }}
      .topbar {{
        position: sticky; top: 0; z-index: 9999;
        height: var(--header-h);
        display: grid; grid-template-columns: 1fr auto; align-items: center;
        padding: 0 12px; background: rgba(18,18,18,.92);
        border-bottom: 1px solid rgba(255,255,255,.08);
        font-family: 'Noto Sans Tamil', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      }}
      .tb-left {{ color:#e8e8e8; font-size:15px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
      .tb-right {{ color:#e8e8e8; font-variant-numeric: tabular-nums; font-size:16px; font-weight:700; margin-left:12px; }}
      main .block-container {{ padding-top: calc(var(--header-h) + 6px) !important; }}
    </style>
    <div class="topbar">
      <div class="tb-left">📅 {left_text}</div>
      <div class="tb-right" id="tbClock">--:--</div>
    </div>
    <script>
      function setClock(){{
        try{{
          const s=new Date().toLocaleTimeString('en-GB',{{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}});
          const el=window.parent.document.getElementById('tbClock')||document.getElementById('tbClock');
          if(el) el.textContent=s;
        }}catch(e){{}}
      }}
      setClock(); setInterval(setClock,1000);
    </script>
    """, unsafe_allow_html=True)
