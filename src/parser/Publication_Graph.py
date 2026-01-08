import json
from collections import defaultdict
from parser.Hierarchy_Tree import Node
from typing import List

class Publication_Graph:
    def __init__(self, pub_id: str):
        self.pub_id = pub_id
        self.elements = {}
        self.hierarchy = defaultdict(dict) 
        self.content_to_id = {} 
        self.counter = 0

    def subtree_signature(self, node: Node) -> str:
        if node.is_leaf():
            return f"<{node.node_type}:{node.report()}>"
        child_sigs = ",".join(self.subtree_signature(c) for c in node.children)
        return f"<{node.node_type}:{node.report()}:[{child_sigs}]>"

    def _generate_element_id(self, node: Node, is_root=False) -> str:
        node_type = node.node_type
        if is_root:
            self.counter += 1
            return f"{self.pub_id}-{node_type}-el{self.counter}"

        sig = self.subtree_signature(node)
        key = (sig, node_type)
        if key in self.content_to_id:
            return self.content_to_id[key]

        self.counter += 1
        element_id = f"{self.pub_id}-{node_type}-el{self.counter}"
        self.content_to_id[key] = element_id
        return element_id

    def _traverse_tree(self, node: Node, version_index: int, parent_id=None, is_root=False):
        element_id = self._generate_element_id(node, is_root=is_root)
        self.elements[element_id] = node.report()
        self.hierarchy[version_index][element_id] = parent_id

        for child in node.children:
            self._traverse_tree(child, version_index, parent_id=element_id)

    def add_tree(self, root: Node, version_index: int):
        self._traverse_tree(root, version_index, parent_id=None, is_root=True)

    def merge_graphs(self, graphs: List["Publication_Graph"], version_indices: List[int]):
        for g, v_idx in zip(graphs, version_indices):
            for ver, hdict in g.hierarchy.items():
                for child_old_id, parent_old_id in hdict.items():
                    # reconstruct Node with children if possible (for subtree_signature)
                    child_node_report = g.elements[child_old_id]
                    child_node = Node("Node", title=child_node_report)
                    child_id = self._generate_element_id(child_node)

                    parent_id = None
                    if parent_old_id:
                        parent_report = g.elements[parent_old_id]
                        parent_node = Node("Node", title=parent_report)
                        parent_id = self._generate_element_id(parent_node)

                    # Set hierarchy for this version
                    self.hierarchy[v_idx][child_id] = parent_id
                    # Add element content if missing
                    self.elements[child_id] = child_node_report

    def export_json(self, path: str):
        hierarchy_dict = {str(v): dict(d) for v, d in self.hierarchy.items()}
        out = {
            "elements": self.elements,
            "hierarchy": hierarchy_dict
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Graph saved to {path}")
