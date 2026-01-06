import json
from collections import defaultdict
from parser.Hierarchy_Tree import Node
from typing import List

# This is the final graph when we merge the trees
class Publication_Graph:
    def __init__(self, pub_id: str):
        self.pub_id = pub_id
        self.elements = {}  # element_id -> report/content
        self.hierarchy = defaultdict(dict)  # version_index -> {child_id: parent_id}
        self.content_to_id = {}  # deduplicate by node.report()
        self.counter = 0

    # Each element(node) will be generated with distinct ID
    def _generate_element_id(self, node_report: str, node_type: str) -> str:
        key = (node_report, node_type)
        if key in self.content_to_id:
            return self.content_to_id[key]

        self.counter += 1
        element_id = f"{self.pub_id}-{node_type}-el{self.counter}"
        self.content_to_id[key] = element_id
        return element_id

    # Traverse the tree for adding elements
    def _traverse_tree(self, node: Node, version_index: int, parent_id=None):
        node_report = node.report()
        node_type = node.node_type
        element_id = self._generate_element_id(node_report, node_type)

        # Add element
        self.elements[element_id] = node_report

        # Record hierarchy for this version
        self.hierarchy[version_index][element_id] = parent_id

        # Recurse on children
        for child in node.children:
            self._traverse_tree(child, version_index, parent_id=element_id)

    # Add a tree
    def add_tree(self, root: Node, version_index: int):
        """Add a tree of a specific version"""
        self._traverse_tree(root, version_index)

    # Merge multi graph
    def merge_graphs(self, graphs: List["Publication_Graph"], version_indices: List[int]):
        for g, v_idx in zip(graphs, version_indices):
            for (old_content, old_type), old_id in g.content_to_id.items():
                eid = self._generate_element_id(old_content, old_type)
                self.elements[eid] = old_content

            for ver, hdict in g.hierarchy.items():
                new_hierarchy = {}
                for child_old_id, parent_old_id in hdict.items():
                    child_content = g.elements[child_old_id]
                    # Extract node_type from old_id
                    node_type = child_old_id.split('-')[1] if '-' in child_old_id else "Node"
                    child_id = self._generate_element_id(child_content, node_type)

                    parent_id = None
                    if parent_old_id:
                        parent_content = g.elements[parent_old_id]
                        parent_type = parent_old_id.split('-')[1] if '-' in parent_old_id else "Node"
                        parent_id = self._generate_element_id(parent_content, parent_type)

                    new_hierarchy[child_id] = parent_id
                self.hierarchy[v_idx].update(new_hierarchy)

    # Export the json files contain the node and edges itself
    def export_json(self, path: str):
        # convert version indices to string keys
        hierarchy_dict = {str(v): dict(d) for v, d in self.hierarchy.items()}
        out = {
            "elements": self.elements,
            "hierarchy": hierarchy_dict
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Graph saved to {path}")
