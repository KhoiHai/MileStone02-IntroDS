import os
import re
from dataclasses import dataclass
from typing import Dict
import bibtexparser

# Class for reference
@dataclass
class Reference_Entry:
    key: str
    entry_type: str
    fields: Dict[str, str]
    source: str

# Regex for .bib parsing
BIB_ENTRY_RE = re.compile(
    r'@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\}', 
    re.DOTALL
)
BIB_FIELD_RE = re.compile(
    r'(\w+)\s*=\s*[\{"]([^}"]+)[\}"]', 
    re.DOTALL
)

# Regex for \bibitem parsing
BIBITEM_RE = re.compile(
    r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\Z)', 
    re.DOTALL
)

# Regex for title detection (handles LaTeX quotes, ASCII quotes, smart quotes, trailing commas)
TITLE_RE = re.compile(
    r'``(.*?)\'\'|'      # LaTeX ``title'' 
    r'``(.*?)",|'        # LaTeX ``title",  (trailing comma)
    r'"(.*?)",'          # ASCII quotes with comma
    r'“(.*?)”|'          # Unicode smart quotes
    r'"(.*?)"',           # ASCII quotes without comma
    re.DOTALL
)

# Parse .bib file content
def parse_bibtex(content: str) -> Dict[str, Reference_Entry]:
    bib_database = bibtexparser.loads(content)
    entries = {}

    for entry in bib_database.entries:
        key = entry.get('ID')  # BibTeX key
        entry_type = entry.get('ENTRYTYPE', 'misc')  # type like article, book, misc
        # copy all other fields except ID and ENTRYTYPE
        fields = {k.lower(): v for k, v in entry.items() if k not in ['ID', 'ENTRYTYPE']}
        entries[key] = Reference_Entry(key=key, entry_type=entry_type, fields=fields, source='bib')

    return entries

# Heuristic parser for \bibitem text
def heuristic_parse_reference(text: str) -> Dict[str, str]:
    fields = {}

    # Year detection
    year_match = re.search(r'(19|20)\d{2}', text)
    if year_match:
        fields["year"] = year_match.group(0)

    # Title detection
    title_match = TITLE_RE.search(text)
    if title_match:
        # pick the first non-None group
        title = next(g for g in title_match.groups() if g)
        fields["title"] = title.strip().rstrip(",")  # remove trailing comma

    # Author detection: everything before the title
    if "title" in fields:
        title_pos = text.find(fields["title"])
        if title_pos > 0:
            author_text = text[:title_pos].rstrip(", ").strip()
            fields["author"] = author_text
        else:
            fields["author"] = text.split(",")[0].strip()
    else:
        # fallback: first part before comma
        parts = text.split(",", 1)
        fields["author"] = parts[0].strip() if parts else ""

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

# Collect references from .bib and .tex files
def collect_references(tex_files) -> Dict[str, Reference_Entry]:
    references = {}

    # First, parse any .bib files
    for f in tex_files:
        if f.endswith(".bib") and os.path.exists(f):
            with open(f, encoding="utf-8", errors="ignore") as fp:
                references.update(parse_bibtex(fp.read()))

    # Then parse \bibitem in .tex files
    for f in tex_files:
        if f.endswith(".tex") and os.path.exists(f):
            with open(f, encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            if "\\bibitem" in content:
                references.update(parse_bibitem_block(content))

    return references

if __name__ == "__main__":
    tex_path = [
        "../../demo-data/2212-11476/tex/2212.11476v1/ref.bib"
    ]
    refs = collect_references(tex_path)
    for k, v in refs.items():
        print(f"{k}: author={v.fields.get('author')}, title={v.fields.get('title')}, year={v.fields.get('year')}")
