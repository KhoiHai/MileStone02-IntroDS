import re
from .cleaning import *

# Chapter, section, subsection and subsubsection regex
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

# Split the text into paragraphs
def split_into_paragraphs(text):
    lines = text.splitlines()
    paragraphs = []
    current = []

    for line in lines:
        if not line.strip(): 
            if current:
                paragraphs.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs

# Parse the title if the node has 
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

# Merge multine math 
def merge_multiline_display_math(text):
    """Merge multi-line \[...\] math into a single line."""
    pattern = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
    def replacer(m):
        content = m.group(1)
        content = re.sub(r'%.*', '', content)
        content = re.sub(r'\s+', ' ', content)
        return f"\\[{content.strip()}\\]"
    return pattern.sub(replacer, text)

def merge_multiline_env_math(text):
    """Merge multi-line \begin{env}...\end{env} math into a single line."""
    pattern = re.compile(
        r'\\begin\{(equation\*?|align\*?|gather|multline)\}(.*?)\\end\{\1\}',
        re.DOTALL
    )
    def replacer(m):
        env = m.group(1)
        content = m.group(2)
        content = re.sub(r'%.*', '', content)       
        content = re.sub(r'\s+', ' ', content)  
        return f"\\begin{{{env}}}{content.strip()}\\end{{{env}}}"
    return pattern.sub(replacer, text)

# Split the paragraph to components 
def split_sentences(text):
    """Split normal text (outside math) into sentences."""
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]

def split_paragraph(paragraph):
    paragraph = paragraph.strip()
    paragraph = merge_multiline_display_math(paragraph)
    paragraph = merge_multiline_env_math(paragraph)

    result = []
    pos = 0

    math_pattern = re.compile(
        r'(\\begin\{(equation|equation\*|align|align\*|gather|multline)\}.*?\\end\{\2\}|\\\[.*?\\\])',
        re.DOTALL
    )

    for m in math_pattern.finditer(paragraph):
        if m.start() > pos:
            before = paragraph[pos:m.start()]
            if before.strip():
                for s in split_sentences(before):
                    result.append(("Sentence", s))
        eq = m.group(0).strip()
        result.append(("Equation", eq))
        pos = m.end()

    if pos < len(paragraph):
        remaining = paragraph[pos:]
        if remaining.strip():
            for s in split_sentences(remaining):
                result.append(("Sentence", s))

    return result