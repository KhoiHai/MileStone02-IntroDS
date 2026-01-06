import os
import re
from dataclasses import dataclass
from typing import Dict
import bibtexparser

# Class for storing reference
@dataclass
class Reference_Entry:
    key: str
    entry_type: str
    fields: Dict[str, str]
    source: str

# The code for parsing the reference inside bib
def parse_bibtex(content: str) -> Dict[str, Reference_Entry]:
    # 1️⃣ Fix bare values like `file = F` -> `file = {F}`
    def wrap_bare_value(match):
        field = match.group(1)
        value = match.group(2).strip()
        # nếu value chưa có {} hoặc ""
        if not (value.startswith("{") or value.startswith('"')):
            value = "{" + value + "}"
        return f"{field} = {value}"

    content_fixed = re.sub(r'(\w+)\s*=\s*([^,}]+)', wrap_bare_value, content)

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = True  # ignore unknown types/macros
    try:
        bib_database = bibtexparser.loads(content_fixed, parser=parser)
    except Exception as e:
        print(f"[WARN] Failed to parse .bib file: {e}")
        return {}

    entries = {}
    for entry in bib_database.entries:
        key = entry.get('ID')
        entry_type = entry.get('ENTRYTYPE', 'misc')
        # giữ nguyên tất cả fields, không lowercase để lưu đúng gốc
        fields = {k: v for k, v in entry.items() if k not in ['ID', 'ENTRYTYPE']}
        entries[key] = Reference_Entry(key=key, entry_type=entry_type, fields=fields, source='bib')
    return entries

# Code for helping cleaning before parsing the tex reference
def clean_latex(text: str) -> str:
    if not text: return ""
    text = re.sub(r'\\\w+\{(.*?)\}', r'\1', text)
    text = text.replace('{', '').replace('}', '')
    text = text.replace('~', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Parsing a single \bibiitem
def parse_single_bibitem(key: str, text: str) -> Reference_Entry:
    text = " ".join(text.split())  # normalize whitespace

    # Searching for matching with title
    title_match = re.search(r'``(.*?)(?:\'\'|,"|")', text)
    if title_match:
        title = title_match.group(1).strip()
        author_part = text[:title_match.start()]
        remainder = text[title_match.end():]
    else:
        parts = text.split(',', 1)
        author_part = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""
        title = ""

    # Determine the year
    years = re.findall(r'\b(?:19|20)\d{2}\b', text)
    year = years[-1] if years else ""

    # Journal
    journal_match = re.search(r'\\textit\{(.*?)\}', text)
    journal = journal_match.group(1) if journal_match else ""
    if not journal and "," in remainder:
        journal_candidate = remainder.split(',')[0].strip()
        if journal_candidate:
            journal = journal_candidate

    fields = {
        "author": clean_latex(author_part).rstrip(',').strip(),
        "title": clean_latex(title),
        "year": year,
        "journal": clean_latex(journal).rstrip(',').strip()
    }

    return Reference_Entry(key=key, entry_type="article", fields=fields, source="bibitem")

# parse every bibitem
def parse_bibitem_block(content: str) -> Dict[str, Reference_Entry]:
    refs = {}
    content = re.sub(r'%.*', '', content)
    content = content.replace('\n', ' ')

    pattern = r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)'
    matches = re.finditer(pattern, content)

    for m in matches:
        key = m.group(1).strip()
        text = m.group(2).strip()
        refs[key] = parse_single_bibitem(key, text)
    return refs

# Collect references
def collect_references(tex_files) -> Dict[str, Reference_Entry]:
    references = {}

    # 1. Parse .bib files
    for f in tex_files:
        if f.endswith(".bib") and os.path.exists(f):
            with open(f, encoding="utf-8", errors="ignore") as fp:
                references.update(parse_bibtex(fp.read()))

    # 2. Parse \bibitem in .tex files
    for f in tex_files:
        if f.endswith(".tex") and os.path.exists(f):
            with open(f, encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            if "\\bibitem" in content:
                print(f"Parsing bibitems in {f}")
                references.update(parse_bibitem_block(content))

    return references

if __name__ == "__main__":
    tex_path = [
        "../../demo-data/2212-11479/tex/2212.11479v1/DifferentialPrivate_Social_network.tex"
    ]
    refs = collect_references(tex_path)
    for k, v in refs.items():
        print(f"{k}: author={v.fields.get('author')}, title={v.fields.get('title')}, year={v.fields.get('year')}")
