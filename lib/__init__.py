# lib/__init__.py
# Keep __init__ tiny so importing `lib` never pulls old names.

from .top_strip import render_top_strip           # top strip (date/time + buttons + loader)
from .qc_state  import render_reference_and_editor  # editor + reference panels

__all__ = [
    "render_top_strip",
    "render_reference_and_editor",
]
