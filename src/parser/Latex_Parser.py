from utils.parsing import *
from utils.post_cleaning import *
from .Hierarchy_Tree import Node, Hierarchy_Tree

class Latex_Parser:
    def __init__(self):
        self.tree = Hierarchy_Tree()
        self.buffer = []  # buffer bình thường
        self.abstract_buffer = []
        self.in_abstract = False
        self.theorem_buffer = []
        self.in_theorem = False
        self.theorem_title = None
        self.lemma_buffer = []
        self.in_lemma = False
        self.lemma_title = None

    def parse(self, text: str):
        text = preprocess_text(text)
        text = extract_document_body(text)
        lines = text.splitlines()

        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue

            # ---------- Abstract ----------
            if ABSTRACT_BEGIN_RE.search(line_strip):
                if self.buffer:
                    self._flush_buffer_as_paragraph(self.buffer)
                    self.buffer = []
                self.in_abstract = True
                self.abstract_buffer = []
                continue

            if ABSTRACT_END_RE.search(line_strip):
                if self.abstract_buffer:
                    self._flush_buffer_as_abstract(self.abstract_buffer)
                    self.abstract_buffer = []
                self.in_abstract = False
                continue

            # ---------- Theorem ----------
            m_theorem = THEOREM_BEGIN_RE.match(line_strip)
            if m_theorem:
                if self.buffer:
                    self._flush_buffer_as_paragraph(self.buffer)
                    self.buffer = []
                self.in_theorem = True
                self.theorem_buffer = []
                self.theorem_title = m_theorem.group(2) or "Theorem"
                continue

            if THEOREM_END_RE.match(line_strip):
                if self.theorem_buffer:
                    self._flush_buffer_as_theorem(self.theorem_buffer, self.theorem_title)
                    self.theorem_buffer = []
                self.in_theorem = False
                self.theorem_title = None
                continue

            # ---------- Lemma ----------
            m_lemma = LEMMA_BEGIN_RE.match(line_strip)
            if m_lemma:
                if self.buffer:
                    self._flush_buffer_as_paragraph(self.buffer)
                    self.buffer = []
                self.in_lemma = True
                self.lemma_buffer = []
                self.lemma_title = m_lemma.group(2) or "Lemma"
                continue

            if LEMMA_END_RE.match(line_strip):
                if self.lemma_buffer:
                    self._flush_buffer_as_lemma(self.lemma_buffer, self.lemma_title)
                    self.lemma_buffer = []
                self.in_lemma = False
                self.lemma_title = None
                continue

            # ---------- Section / Chapter ----------
            level, title = parse_title(line_strip)
            if level:
                if self.buffer:
                    self._flush_buffer_as_paragraph(self.buffer)
                    self.buffer = []
                self.tree.add_hierarchy_node(level, title)
                continue

            # ---------- Normal line ----------
            if self.in_abstract:
                self.abstract_buffer.append(line_strip)
            elif self.in_theorem:
                self.theorem_buffer.append(line_strip)
            elif self.in_lemma:
                self.lemma_buffer.append(line_strip)
            else:
                self.buffer.append(line_strip)

        # ---------- Flush remaining ----------
        if self.buffer:
            self._flush_buffer_as_paragraph(self.buffer)
        if self.abstract_buffer:
            self._flush_buffer_as_abstract(self.abstract_buffer)
        if self.theorem_buffer:
            self._flush_buffer_as_theorem(self.theorem_buffer, self.theorem_title)
        if self.lemma_buffer:
            self._flush_buffer_as_lemma(self.lemma_buffer, self.lemma_title)

        self.tree.root.clean_children()
        return self.tree.root

    # ---------- Flush helpers ----------
    def _flush_buffer_as_paragraph(self, buffer):
        text = "\n".join(buffer).strip()
        if not text:
            return
        paragraph_node = Node("Paragraph", title="Paragraph")
        for node_type, content in split_paragraph(text):
            child_node = Node(node_type, content=content)
            paragraph_node.add_child(child_node)
        self.tree.stack[-1].add_child(paragraph_node)

    def _flush_buffer_as_abstract(self, buffer):
        text = "\n".join(buffer).strip()
        if not text:
            return
        abstract_node = Node("Abstract", title="Abstract")
        for node_type, content in split_paragraph(text):
            child_node = Node(node_type, content=content)
            abstract_node.add_child(child_node)
        self.tree.stack[-1].add_child(abstract_node)

    def _flush_buffer_as_theorem(self, buffer, title):
        text = "\n".join(buffer).strip()
        if not text:
            return
        theorem_node = Node("Theorem", title=title)
        for node_type, content in split_paragraph(text):
            child_node = Node(node_type, content=content)
            theorem_node.add_child(child_node)
        self.tree.stack[-1].add_child(theorem_node)

    def _flush_buffer_as_lemma(self, buffer, title):
        text = "\n".join(buffer).strip()
        if not text:
            return
        lemma_node = Node("Lemma", title=title)
        for node_type, content in split_paragraph(text):
            child_node = Node(node_type, content=content)
            lemma_node.add_child(child_node)
        self.tree.stack[-1].add_child(lemma_node)
