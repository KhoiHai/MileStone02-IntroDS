from utils.post_cleaning import *
import re
from typing import Dict, List 

# Class for Node
class Node:
    def __init__(self, node_type, title=None, content=None):
        self.node_type = node_type # The node type such as: section, subsection, subsubsection, chapter, mathblock or something
        self.title = title # This is for the title node 
        self.content = content # This is for the content node
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def is_leaf(self):
        return self.content is not None
    
    def clean_children(self):
        cleaned = []

        for child in self.children:
            child.clean_children()

            if child.is_leaf():
                content = child.content.strip()

                if content.startswith('%'):
                    continue
                
                # Clean the sentence
                if child.node_type == "Sentence":
                    content = clean_sentence(content)
                    if not content:
                        continue
                    child.content = content

                if not content:
                    continue

            cleaned.append(child)

        self.children = cleaned

    def update_cite_keys(self, key_map: Dict[str, str]):
        CITE_RE = re.compile(r'\\cite\{([^}]+)\}')
        
        if self.is_leaf() and self.node_type == "Sentence":
            def repl(m):
                old_keys = [k.strip() for k in m.group(1).split(",")]
                new_keys = [key_map.get(k, k) for k in old_keys]
                return r"\cite{" + ",".join(new_keys) + "}"
            self.content = CITE_RE.sub(repl, self.content)
        
        for child in self.children:
            child.update_cite_keys(key_map)

    def count_nodes(self) -> int:
        count = 1 
        for child in self.children:
            count += child.count_nodes()
        return count

    '''
    def report(self):
        if self.is_leaf():
            return f"<{self.node_type}: {self.content}>"
        return f"<{self.node_type}: {self.title}>"
    '''
    def report(self):
        if self.is_leaf():
            return f"{self.content}"
        return f"{self.title}"

# Class for Hierarchy Tree 
class Hierarchy_Tree:
    def __init__(self):
        self.root = Node("Document", title="Document")
        self.stack = [self.root]

    # Add the node itself does not has the end and the begin
    def add_hierarchy_node(self, level, title):
        node = Node(level, title=title)
        while len(self.stack) > self._level(level):
            self.stack.pop()
        self.stack[-1].add_child(node)
        self.stack.append(node)

    # Container node with pre-parsed children (Theorem, Lemma, Abstract)
    def add_container_node(self, node_type, title, children_list):
        node = Node(node_type, title=title)
        for item in children_list:
            if isinstance(item, Node):
                node.add_child(item)
            else:
                t, c = item
                node.add_child(Node(t, content=c))
        self.stack[-1].add_child(node)
        return node

    # Leaf node
    def add_leaf(self, node_type, content):
        node = Node(node_type, content=content)
        self.stack[-1].add_child(node)

    def total_nodes(self) -> int:
        return self.root.count_nodes()

    def _level(self, level):
        return {
            "Chapter": 2,
            "Section": 3,
            "Subsection": 4,
            "Subsubsection": 5,
        }.get(level, 99)
