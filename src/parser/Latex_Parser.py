from utils.parsing import *
from utils.post_cleaning import *
from .Hierarchy_Tree import Node, Hierarchy_Tree

class Latex_Parser:
    def __init__(self):
        self.tree = Hierarchy_Tree()

    def parse(self, text: str):
        # Pre cleaning
        text = preprocess_text(text)
        text = extract_document_body(text)

        paragraphs = split_into_paragraphs(text)

        for block in paragraphs:
            block_strip = block.strip()
            lines = block_strip.splitlines()
            first_line = lines[0].strip()

            # Abstract
            if ABSTRACT_BEGIN_RE.search(block_strip):
                children = split_paragraph(block)
                self.tree.add_container_node("Abstract", "Abstract", children)
                continue

            # Appendix
            if APPENDIX_RE.search(block_strip):
                self.tree.add_hierarchy_node("Section", "Appendix")
                continue

            # Section hierarchy
            level, title = parse_title(first_line)
            if level:
                self.tree.add_hierarchy_node(level, title)
                continue

            # Theorem
            if THEOREM_BEGIN_RE.match(first_line):
                m = THEOREM_BEGIN_RE.match(first_line)
                title = m.group(2) or "Theorem"
                children = split_paragraph(block)
                self.tree.add_container_node("Theorem", title, children)
                continue

            # Lemma
            if LEMMA_BEGIN_RE.match(first_line):
                m = LEMMA_BEGIN_RE.match(first_line)
                title = m.group(2) or "Lemma"
                children = split_paragraph(block)
                self.tree.add_container_node("Lemma", title, children)
                continue

            # Figure / Table (atomic blocks)
            if FIGURE_BEGIN_RE.search(block_strip):
                self.tree.add_leaf("Figure", block_strip)
                continue

            if TABLE_BEGIN_RE.search(block_strip):
                self.tree.add_leaf("Table", block_strip)
                continue

            for node_type, content in split_paragraph(block):
                self.tree.add_leaf(node_type, content)

        # Post cleaning
        self.tree.root.clean_children()
        return self.tree.root
