import os
from utils.collect_tex_file import collect_tex_file, dfs_collect
from parser.Latex_Parser import Latex_Parser
from utils.reference_extraction import collect_references, Reference_Entry
from utils.deduplicate_reference import canonical_ref_id, deduplicate_references
from parser.Hierarchy_Tree import Node, Hierarchy_Tree
from parser.Publication_Graph import Publication_Graph

# ---------- Build tree & extract references for one version ----------
def build_tree_and_refs(tex_dir):
    # DFS collect tex files for building tree
    main_tex, _ = collect_tex_file(tex_dir)
    if not main_tex:
        print(f"[WARN] No main tex file found in {tex_dir}")
        return None, {}

    tex_files = dfs_collect(main_tex)  # only .tex files
    if not tex_files:
        print(f"[WARN] No tex files collected from {main_tex}")
        return None, {}

    # Parse each tex file into tree
    parser = Latex_Parser()
    for f in tex_files:
        try:
            with open(f, encoding="utf-8", errors="ignore") as fp:
                parser.parse(fp.read())
        except Exception as e:
            print(f"[ERROR] Failed to parse {f}: {e}")

    # Collect all tex + bib files for references
    all_files_for_refs = []
    for root, _, files in os.walk(tex_dir):
        for f in files:
            if f.endswith(".tex") or f.endswith(".bib"):
                all_files_for_refs.append(os.path.join(root, f))

    # Extract references
    refs = collect_references(all_files_for_refs)
    return parser.tree.root, refs

# ---------- Update \cite{} recursively ----------
def update_tree_cites(tree_root: Node, key_map: dict):
    tree_root.update_cite_keys(key_map)

# ---------- Print tree ----------
def print_tree(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{node.report()}")
    for child in node.children:
        print_tree(child, indent + 1)

# ---------- Verify full-text deduplication ----------
def verify_deduplication(pub_graph: Publication_Graph):
    version_ids = list(pub_graph.hierarchy.keys())
    print(f"Versions in graph: {version_ids}")
    all_nodes = set(pub_graph.elements.keys())
    print(f"Total unique nodes in elements: {len(all_nodes)}")

    # Build a map: element_id -> list of versions where it appears
    element_versions = {eid: [] for eid in all_nodes}
    for v in version_ids:
        for child_id in pub_graph.hierarchy[v]:
            element_versions[child_id].append(v)

    # Count nodes that appear in more than 1 version
    shared_nodes = {eid: vers for eid, vers in element_versions.items() if len(vers) > 1}

    print(f"Number of nodes shared across multiple versions: {len(shared_nodes)}")
    if shared_nodes:
        print("Sample shared nodes (element_id -> versions):")
        for i, (eid, vers) in enumerate(shared_nodes.items()):
            print(f"  {eid} -> {vers}")
            if i >= 9:  # print max 10 examples
                break

# ---------- Main test ----------
if __name__ == "__main__":
    # Example: paths to two versions
    versions = [
        "../demo-data/2212-11476/tex/2212.11476v1",
        "../demo-data/2212-11476/tex/2212.11476v2"
    ]

    all_trees = []
    all_refs = {}

    # 1. Build trees & extract references
    for v in versions:
        print(f"\n--- Processing version: {v} ---")
        tree_root, refs = build_tree_and_refs(v)
        if tree_root:
            all_trees.append(tree_root)
        all_refs.update(refs)

    # 2. Deduplicate references to create canonical keys
    canonical_refs, key_map, simlist = deduplicate_references(all_refs)

    print("\n--- Canonical References ---")
    for cid, ref in canonical_refs.items():
        print(f"[{ref.source}] {ref.key} -> fields: {ref.fields}")

    # 3. Update \cite{} in all trees
    for tree_root in all_trees:
        update_tree_cites(tree_root, key_map)

    # 4. Build graph
    graph = Publication_Graph(pub_id="2212.11476")
    graph.add_tree(all_trees[0], version_index=1)
    graph.add_tree(all_trees[1], version_index=2)

    # 5. Export JSON
    graph.export_json("hierarchy.json")

    # 6. Verify full-text deduplication
    print("\n--- Verifying full-text deduplication ---")
    verify_deduplication(graph)
