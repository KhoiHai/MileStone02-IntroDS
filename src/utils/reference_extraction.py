import os
import re
from dataclasses import dataclass
from typing import Dict

@dataclass
class Reference_Entry:
    key: str
    entry_type: str
    fields: Dict[str, str]
    source: str

# Regex \bibitem block
BIBITEM_RE = re.compile(
    r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\Z)',
    re.DOTALL
)

# Title regex: LaTeX ``title'' or ASCII quotes "title" or smart quotes “title”
TITLE_RE = re.compile(
    r'``([^`]+)\'\'|'      # LaTeX quotes
    r'"([^"]+)"|'           # ASCII quotes
    r'“([^”]+)”',           # smart quotes
    re.DOTALL
)

# Heuristic parse
def heuristic_parse_reference(text: str) -> Dict[str, str]:
    fields = {}

    # Title first
    title_match = TITLE_RE.search(text)
    if title_match:
        title = next(g for g in title_match.groups() if g)
        fields["title"] = title.strip()

        # Author is everything before title
        title_pos = text.find(title)
        if title_pos > 0:
            author_text = text[:title_pos].rstrip(", ").strip()
            fields["author"] = author_text
    else:
        # fallback: first part before comma
        parts = text.split(",", 1)
        fields["author"] = parts[0].strip() if parts else ""

    # Year
    year_match = re.search(r'(19|20)\d{2}', text)
    if year_match:
        fields["year"] = year_match.group(0)

    return fields

# Parse \bibitem blocks
def parse_bibitem_block(content: str) -> Dict[str, Reference_Entry]:
    refs = {}
    for m in BIBITEM_RE.finditer(content):
        key = m.group(1).strip()
        text = m.group(2).strip()
        fields = heuristic_parse_reference(text)
        refs[key] = Reference_Entry(key=key, entry_type="misc", fields=fields, source="bibitem")
    return refs

# Collect references
def collect_references(tex_files) -> Dict[str, Reference_Entry]:
    references = {}
    for f in tex_files:
        if f.endswith(".tex") and os.path.exists(f):
            with open(f, encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            if "\\bibitem" in content:
                references.update(parse_bibitem_block(content))
    return references

if __name__ == "__main__":
    tex_path = [
        "../../demo-data/2212-11479/tex/2212.11479v1/DifferentialPrivate_Social_network.tex"
    ]
    refs = collect_references(tex_path)
    for k, v in refs.items():
        print(f"{k}: author={v.fields.get('author')}, title={v.fields.get('title')}, year={v.fields.get('year')}")
