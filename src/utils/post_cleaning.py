import re

# Structural environment
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

# Formating and useless command
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

MULTISPACE_RE = re.compile(r"\s+")

CONTROL_COMMANDS_RE = re.compile(
    r"""
    \\(ifpreprint|fi|clearpage|newpage|ignorespaces)
    """,
    re.VERBOSE
)

# Check the inline math to not to delete the command inside
INLINE_MATH_RE = re.compile(
    r"""
    (\${1,2}.*?\${1,2}     # $...$ or $$...$$
    |\\\(.*?\\\)          # \( ... \)
    |\\\[.*?\\\])         # \[ ... \]
    """,
    re.VERBOSE | re.DOTALL
)

# Post cleaning the sentence
def clean_sentence(text: str) -> str:
    if not text:
        return ""

    s = text.strip()

    # Keep the math block
    math_blocks = []

    def _protect_math(m):
        math_blocks.append(m.group(0))
        return f"__MATH_{len(math_blocks)-1}__"

    s = INLINE_MATH_RE.sub(_protect_math, s)

    # Remove the structural wrapper but keeping the content
    s = STRUCTURAL_BEGIN_RE.sub("", s)
    s = STRUCTURAL_END_RE.sub("", s)

    # Removing useless command
    s = USELESS_COMMANDS_RE.sub("", s)

    # Removing float specifiers
    s = FLOAT_SPEC_RE.sub("", s)

    # Unwrap the text formating
    s = re.sub(
        r"\\(text|emph|textbf|textit|underline)\{([^}]*)\}",
        r"\2",
        s
    )

    # Unwrap the metadata
    s = re.sub(r"\\keywords\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\amscode\{[^}]*\}", "", s)

    # Removing control command 
    s = CONTROL_COMMANDS_RE.sub("", s)
    s = re.sub(
        r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}",
        r"\1",
        s
    )

    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)

    # Normalize space
    s = MULTISPACE_RE.sub(" ", s).strip()

    # Restore the math blocks
    for i, m in enumerate(math_blocks):
        s = s.replace(f"__MATH_{i}__", m)

    if len(s) < 1:
        return ""
    
    return s