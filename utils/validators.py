# utils/validators.py

import re
from datetime import datetime

def is_valid_date(s: str, fmt="%Y-%m-%d"):
    try:
        datetime.strptime(s, fmt)
        return True
    except ValueError:
        return False

def is_positive_number(s: str):
    try:
        return float(s) >= 0
    except ValueError:
        return False

def is_nonempty_text(s: str):
    return bool(s and s.strip())

def matches_pattern(s: str, pattern: str):
    return re.match(pattern, s) is not None
