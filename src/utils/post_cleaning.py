import re


# Structural Environment
STRUCTURAL_BEGIN_RE = re.compile(
    r"""
    \\begin\{
        (abstract|theorem|lemma|proof|remark|definition|example)
    \}
    (?:\[[^\]]*\])?
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

# Formatting and Useless Command
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


# Inline Math should not be cleaned
INLINE_MATH_RE = re.compile(
    r"""
    (\${1,2}.*?\${1,2}     # $...$ or $$...$$
    |\\\(.*?\\\)          # \( ... \)
    |\\\[.*?\\\])         # \[ ... \]
    """,
    re.VERBOSE | re.DOTALL
)

# This is labeling and reference should not be cleaned
SEMANTIC_COMMAND_RE = re.compile(
    r"""
    \\(label|ref|eqref|cite|citep|citet)
    (\[[^\]]*\])?
    \{[^}]*\}
    """,
    re.VERBOSE
)

# Post cleaning
def clean_sentence(text: str) -> str:
    if not text:
        return ""

    s = text.strip()

    math_blocks = []

    def _protect_math(m):
        math_blocks.append(m.group(0))
        return f"__MATH_{len(math_blocks)-1}__"

    s = INLINE_MATH_RE.sub(_protect_math, s)

    semantic_blocks = []

    def _protect_semantic(m):
        semantic_blocks.append(m.group(0))
        return f"__SEM_{len(semantic_blocks)-1}__"

    s = SEMANTIC_COMMAND_RE.sub(_protect_semantic, s)

    s = STRUCTURAL_BEGIN_RE.sub("", s)
    s = STRUCTURAL_END_RE.sub("", s)

    s = USELESS_COMMANDS_RE.sub("", s)
    s = FLOAT_SPEC_RE.sub("", s)
    s = CONTROL_COMMANDS_RE.sub("", s)

    s = re.sub(
        r"\\(text|emph|textbf|textit|underline)\{([^}]*)\}",
        r"\2",
        s
    )

    s = re.sub(r"\\keywords\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\amscode\{[^}]*\}", "", s)

    s = re.sub(
        r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}",
        r"\1",
        s
    )

    # Remove leftover commands without arguments
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)
    s = MULTISPACE_RE.sub(" ", s).strip()

    for i, m in enumerate(semantic_blocks):
        s = s.replace(f"__SEM_{i}__", m)

    for i, m in enumerate(math_blocks):
        s = s.replace(f"__MATH_{i}__", m)

    return s if s else ""