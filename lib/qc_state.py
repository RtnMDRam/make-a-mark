import streamlit as st

# ===== CSS for layout and borders =====
_LAYOUT_CSS = """
<style>
.block-container {
    padding-top: 12px;
    padding-bottom: 12px;
}

.section {
    border: 2px solid #2f61c1;   /* default blue */
    border-radius: 12px;
    padding: 10px 12px;
    margin: 0;
}
.section + .section {
    margin-top: 8px;             /* small gap between stacked boxes */
}
.section.ta {
    border-color: #2e7d32;       /* Tamil reference = green */
}
.section.en {
    border-color: #2f61c1;       /* English reference = blue */
}
.section.ed {
    border-color: #2f61c1;       /* SME edit = blue */
}
.section .title {
    font-size: 12px;
    font-weight: 600;
    margin: 0 0 4px 0;
    line-height: 1;
}
</style>
"""

# ===== Helper functions for section wrappers =====
def _section_open(cls: str, title: str):
    st.markdown(
        f"""<div class="section {cls}">
               <div class="title">{title}</div>""",
        unsafe_allow_html=True,
    )

def _section_close():
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Dummy placeholders for your real content renderers =====
def _editor_tamil():
    st.text_area("Editable Tamil Content (SME Panel)", "", height=200)

def _reference_tamil():
    st.markdown("**Non-editable Tamil Reference Content will appear here.**")

def _reference_english():
    st.markdown("**Non-editable English Reference Content will appear here.**")

# ===== Final Layout Renderer =====
def render_reference_and_editor():
    """
    FINAL ORDER (fixed):
    1) TOP: SME Edit (Tamil)  -> blue box
    2) MIDDLE: Tamil reference -> green box
    3) BOTTOM: English reference -> blue box
    """
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    # TOP: SME edit (Tamil)
    _section_open("ed", "SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()

    # MIDDLE: Tamil non-editable
    _section_open("ta", "தமிழ் மூலப் பதிவு")
    _reference_tamil()
    _section_close()

    # BOTTOM: English non-editable
    _section_open("en", "English Version")
    _reference_english()
    _section_close()
