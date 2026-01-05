import re

# Function to clean sentence node by removing comment and unnecessary command line
def filter_sentence_node(text: str) -> str:
    if not text or len(text.strip()) == 0:
        return None

    text = text.strip()

    # Remove pure comment lines
    if text.startswith('%'):
        return None

    # Remove lines that are only commands, but keep content inside braces
    # e.g., \title{...} -> keep the inside
    m = re.match(r'\\[a-zA-Z]+\*?(?:\[.*?\])?\{(.*?)\}', text)
    if m:
        return m.group(1).strip()

    # Remove simple commands without content
    if text.startswith('\\') and '{' not in text and '[' not in text:
        return None

    # Remove lines like \end{lemma}, \begin{theorem} etc.
    if re.match(r'\\(begin|end)\{.*?\}', text):
        return None

    return text if len(text) > 0 else None