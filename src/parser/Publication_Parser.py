import os
from parser.Hierarchy_Tree import Node
from utils.collect_tex_file import collect_tex_file, dfs_collect
from parser.Latex_Parser import Latex_Parser
from utils.reference_extraction import collect_references, Reference_Entry
from parser.Publication_Graph import Publication_Graph
from utils.deduplicate_reference import *

class Publication_Parser:
    """
    Parse one publication folder:
    - Detect versions
    - Build trees per version
    - Merge trees into graph
    - Extract and deduplicate references
    """

    def __init__(self, pub_id: str, pub_path: str):
        self.pub_id = pub_id
        self.pub_path = pub_path
        self.trees = []          # list of Node (root per version)
        self.references = {}     # all references (before dedup)
        self.graph = Publication_Graph(pub_id=pub_id)

    def parse_dataset(self):
        """Quét tất cả version, build tree, collect references"""
        tex_root = os.path.join(self.pub_path, "tex")
        if not os.path.exists(tex_root):
            print(f"[WARN] No tex folder in {self.pub_path}")
            return

        # 1️⃣ Tìm tất cả version
        versions = [f for f in os.listdir(tex_root) if os.path.isdir(os.path.join(tex_root, f))]
        versions.sort()

        # 2️⃣ Build tree và collect reference cho từng version
        for idx, v in enumerate(versions, start=1):
            version_path = os.path.join(tex_root, v)
            print(f"[INFO] Processing version {v}")

            # DFS collect tex files
            main_tex, _ = collect_tex_file(version_path)
            if not main_tex:
                print(f"[WARN] No main tex in {version_path}")
                continue
            tex_files = dfs_collect(main_tex)

            # Build tree
            parser = Latex_Parser()
            for f in tex_files:
                try:
                    with open(f, encoding="utf-8", errors="ignore") as fp:
                        parser.parse(fp.read())
                except Exception as e:
                    print(f"[ERROR] Failed to parse {f}: {e}")

            tree_root = parser.tree.root
            self.trees.append(tree_root)

            # Collect references from all .tex/.bib in this version
            all_files = []
            for root, _, files in os.walk(version_path):
                for file in files:
                    if file.endswith(".tex") or file.endswith(".bib"):
                        all_files.append(os.path.join(root, file))
            refs = collect_references(all_files)
            self.references.update(refs)

        # 3️⃣ Deduplicate references across all versions
        canonical_refs, key_map, _ = deduplicate_references(self.references)
        self.references = canonical_refs

        # 4️⃣ Update \cite{} in all trees according to canonical references
        for tree_root in self.trees:
            tree_root.update_cite_keys(key_map)

        # 5️⃣ Add all trees to graph (full-text dedup works here)
        for idx, tree_root in enumerate(self.trees, start=1):
            self.graph.add_tree(tree_root, version_index=idx)

    def export_json(self, path: str):
        """Export merged graph to JSON"""
        self.graph.export_json(path)

    def export_bib(self, path: str):
        """Export all references (canonical) to .bib"""
        with open(path, "w", encoding="utf-8") as f:
            for key, ref in self.references.items():
                f.write(f"@{ref.entry_type}{{{key},\n")  # dùng key gốc
                if hasattr(ref, "merged_from") and ref.merged_from:
                    f.write(f"  % Merged from: {', '.join(ref.merged_from)}\n")
                for k, v in ref.fields.items():
                    f.write(f"  {k} = {{{v}}},\n")
                f.write("}\n\n")
        print(f"[INFO] References saved to {path}")