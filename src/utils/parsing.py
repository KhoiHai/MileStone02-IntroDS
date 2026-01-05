import re

# Chapter, Section, Subsection and Subsubsection Regex
CHAPTER_RE = re.compile(r'\\chapter\*?\{(.+?)\}')
SECTION_RE = re.compile(r'\\section\*?\{(.+?)\}')
SUBSECTION_RE = re.compile(r'\\subsection\*?\{(.+?)\}')
SUBSUBSECTION_RE = re.compile(r'\\subsubsection\*?\{(.+?)\}')

# Abstract and Appendix Regex
ABSTRACT_BEGIN_RE = re.compile(r'\\begin\{abstract\}')
ABSTRACT_END_RE = re.compile(r'\\end\{abstract\}')
APPENDIX_RE = re.compile(r'\\appendix')

# Math Block Regex
BLOCK_MATH_BEGIN_RE = re.compile(
    r'\\begin\{(equation|equation\*|align|align\*|gather|multline)\}'
)
BLOCK_MATH_END_RE = re.compile(
    r'\\end\{(equation|equation\*|align|align\*|gather|multline)\}'
)

INLINE_DISPLAY_MATH_RE = re.compile(
    r'(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{(equation|equation\*|align|align\*|gather|multline)\}.*?\\end\{\2\})',
    re.DOTALL
)

# Figure Regex
FIGURE_BEGIN_RE = re.compile(r'\\begin\{figure\*?\}')
FIGURE_END_RE = re.compile(r'\\end\{figure\*?\}')

# Table Regex
TABLE_BEGIN_RE = re.compile(r'\\begin\{table\*?\}')
TABLE_END_RE = re.compile(r'\\end\{table\*?\}')

# Theorem and Lemma Regex
THEOREM_BEGIN_RE = re.compile(r'\\begin\{theorem\}(\[(.*?)\])?')
THEOREM_END_RE = re.compile(r'\\end\{theorem\}')
LEMMA_BEGIN_RE = re.compile(r'\\begin\{lemma\}(\[(.*?)\])?')
LEMMA_END_RE = re.compile(r'\\end\{lemma\}')

# Parsing the title of the container node
def parse_title(line):
    for regex, level in [
        (CHAPTER_RE, "Chapter"),
        (SECTION_RE, "Section"),
        (SUBSECTION_RE, "Subsection"),
        (SUBSUBSECTION_RE, "Subsubsection"),
    ]:
        m = regex.match(line)
        if m:
            return level, m.group(1)
    return None, None

# Parsing the plot of the given container node
def parse_block(lines, i, begin_re, end_re):
    block = [lines[i]]
    i += 1
    while i < len(lines) and not end_re.search(lines[i]):
        block.append(lines[i])
        i += 1
    if i < len(lines):
        block.append(lines[i])
    content = "\n".join(block)
    return content, i + 1

# Splitting the sentences along with math block inside
def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 3]

def merge_multiline_display_math(text):
    pattern = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
    def replacer(m):
        content = m.group(1).replace("\n", " ").strip()
        return f"\\[{content}\\]"
    return pattern.sub(replacer, text)

def split(text):
    # Merge multiline \[ ... \] first
    text = merge_multiline_display_math(text)

    result = []
    pos = 0

    # Regex match all math types
    pattern = re.compile(
        r'(\\begin\{(equation|equation\*|align|align\*|gather|multline)\}.*?\\end\{\2\})'  # \begin{...}...\end{...}
        r'|(\$\$.*?\$\$)'                       # $$...$$
        r'|(\\\[.*?\\\])',                      # \[...\]
        re.DOTALL
    )

    for m in pattern.finditer(text):
        # Text before math block
        if m.start() > pos:
            before = text[pos:m.start()]
            for s in split_sentences(before):
                result.append(("Sentence", s))

        # Math block matched
        eq = m.group(1) or m.group(3) or m.group(4)
        result.append(("Equation", eq))

        pos = m.end()

    # Remaining text after last math block
    if pos < len(text):
        remaining = text[pos:]
        for s in split_sentences(remaining):
            result.append(("Sentence", s))

    return result