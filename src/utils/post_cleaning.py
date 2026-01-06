import re

# Structural Regex
STRUCTURAL_BEGIN_RE = re.compile(
    r"""
    \\begin\{
        (abstract|theorem|lemma|proof|remark|definition|example)
    \}
    (?:\[[^\]]*\])?
    (?:\\label\{[^}]*\})?
    """,
    re.VERBOSE | re.DOTALL
)

STRUCTURAL_END_RE = re.compile(
    r"""
    \\end\{
        (abstract|theorem|lemma|proof|remark|definition|example)
    \}
    """,
    re.VERBOSE | re.DOTALL
)

# Formating or Useless Command Regex
USELESS_COMMANDS_RE = re.compile(
    r"""
    \\centering|
    \\raggedright|
    \\raggedleft|
    \\small|
    \\footnotesize|
    \\scriptsize|
    \\tiny|
    \\normalsize|
    \\large|
    \\Large|
    \\LARGE|
    \\huge|
    \\Huge|
    \\bfseries|
    \\itshape|
    \\rmfamily|
    \\sffamily|
    \\ttfamily|
    \\midrule|
    \\toprule|
    \\bottomrule
    """,
    re.VERBOSE
)

FLOAT_SPEC_RE = re.compile(r"\[[htbpH!]+\]")

# Latex Command Regex
ANY_COMMAND_RE = re.compile(
    r"""
    \\[a-zA-Z]+        # \command
    (\*?)              # optional *
    (\[[^\]]*\])?     # optional [...]
    (\{[^}]*\})?      # optional {...}
    """,
    re.VERBOSE | re.DOTALL
)

MULTISPACE_RE = re.compile(r"\s+")

# Clean the sentence
def clean_sentence(text: str) -> str:
    if not text:
        return ""

    s = text.strip()

    # 0. Early reject: raw LaTeX command → DROP
    if ANY_COMMAND_RE.search(s):
        return ""

    # 1. remove structural begin/end (safety)
    s = STRUCTURAL_BEGIN_RE.sub("", s)
    s = STRUCTURAL_END_RE.sub("", s)

    # 2. remove useless formatting commands
    s = USELESS_COMMANDS_RE.sub("", s)

    # 3. remove float specifiers
    s = FLOAT_SPEC_RE.sub("", s)

    # 4. FINAL CHECK: nếu cleanup xong mà vẫn còn command → DROP
    if ANY_COMMAND_RE.search(s):
        return ""

    # 5. normalize whitespace
    s = MULTISPACE_RE.sub(" ", s).strip()

    return s
