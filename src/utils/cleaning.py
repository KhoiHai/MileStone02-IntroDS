import re

# Removing the comments
def remove_comments(line: str) -> str:
    return line.split("%")[0].rstrip()

# If the comment is alone itself we need to remove and merge the empty line between
def preprocess_text(text: str) -> str:
    lines = text.splitlines()
    out = []

    for line in lines:
        stripped = line.strip()

        # Drop comment-only lines
        if stripped.startswith("%"):
            continue

        # Keep everything else untouched
        out.append(line)

    return "\n".join(out)