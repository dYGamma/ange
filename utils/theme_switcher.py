# utils/theme_switcher.py

import qt_material

THEMES = ["light_blue.xml", "dark_teal.xml"]

def apply_theme(app, theme_name: str):
    """Применяет одну из предустановленных тем."""
    if theme_name not in THEMES:
        theme_name = THEMES[0]
    qt_material.apply_stylesheet(app, theme_name)
