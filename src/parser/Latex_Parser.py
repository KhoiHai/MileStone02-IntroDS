from utils.parsing import *
from utils.cleaning import *
from .Hierarchy_Tree import Node, Hierarchy_Tree

class Latex_Parser:
    def __init__(self):
        self.tree = Hierarchy_Tree()

    def parse(self, text: str):
        lines = text.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Abstract (container with children)
            if ABSTRACT_BEGIN_RE.search(line):
                content, i = parse_block(lines, i, ABSTRACT_BEGIN_RE, ABSTRACT_END_RE)
                children = split(content)
                self.tree.add_container_node("Abstract", "Abstract", children)
                continue

            # Appendix (treated as top-level section, children later)
            if APPENDIX_RE.search(line):
                self.tree.add_hierarchy_node("Section", "Appendix")
                i += 1
                continue

            # Section hierarchy
            level, title = parse_title(line)
            if level:
                self.tree.add_hierarchy_node(level, title)
                i += 1
                continue

            # Theorem
            if THEOREM_BEGIN_RE.match(line):
                m_th = THEOREM_BEGIN_RE.match(line)
                title = m_th.group(2) or "Theorem"
                content, i = parse_block(lines, i, THEOREM_BEGIN_RE, THEOREM_END_RE)
                children = split(content)
                self.tree.add_container_node("Theorem", title, children)
                continue

            # Lemma
            if LEMMA_BEGIN_RE.match(line):
                m_lm = LEMMA_BEGIN_RE.match(line)
                title = m_lm.group(2) or "Lemma"
                content, i = parse_block(lines, i, LEMMA_BEGIN_RE, LEMMA_END_RE)
                children = split(content)
                self.tree.add_container_node("Lemma", title, children)
                continue

            # Block math
            if BLOCK_MATH_BEGIN_RE.search(line):
                content, i = parse_block(lines, i, BLOCK_MATH_BEGIN_RE, BLOCK_MATH_END_RE)
                self.tree.add_leaf("Equation", content)
                continue

            # Figure / Table
            if FIGURE_BEGIN_RE.search(line) or TABLE_BEGIN_RE.search(line):
                end_re = FIGURE_END_RE if FIGURE_BEGIN_RE.search(line) else TABLE_END_RE
                content, i = parse_block(lines, i, FIGURE_BEGIN_RE if FIGURE_BEGIN_RE.search(line) else TABLE_BEGIN_RE, end_re)
                self.tree.add_leaf("Figure", content)
                continue

            # Regular paragraph / sentences / inline math
            if line:
                for node_type, content in split(line):
                    self.tree.add_leaf(node_type, content)
            i += 1

        return self.tree.root