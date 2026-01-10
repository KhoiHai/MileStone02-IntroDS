import re
from typing import Dict, List, Tuple, Optional

LATEX_CMD = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?")
PUNCT = re.compile(r"[^a-z0-9\s]+")
    
def strip_latex(s: str) -> str:
    if s is None:
        return ""
    s = LATEX_CMD.sub(" ", s)
    s = s.replace("{", " ").replace("}", " ").replace("$", " ")
    return s

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = strip_latex(str(s)).lower()
    s = PUNCT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str) -> List[str]:
    s = normalize_text(s)
    return s.split() if s else []

def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def safe_int(x) -> Optional[int]:
    try:
        if x is None:
            return None
        x = str(x).strip()
        if not x:
            return None
        return int(float(x))
    except Exception:
        return None