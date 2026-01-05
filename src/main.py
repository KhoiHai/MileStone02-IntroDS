import os
from utils.collect_tex_file import collect_tex_file, dfs_collect
from parser.Latex_Parser import Latex_Parser

def build_document_tree(tex_dir):
    # Collect main tex file and included files in DFS order
    main_tex, _ = collect_tex_file(tex_dir)
    if not main_tex:
        print(f"[WARN] No main tex file found in {tex_dir}")
        return None

    files = dfs_collect(main_tex)  

    if not files:
        print(f"[WARN] No tex files collected from {main_tex}")
        return None

    # Initialize Latex Parser
    parser = Latex_Parser()

    # Parse each file in DFS order
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="ignore") as fp:
                text = fp.read()
                parser.parse(text)
        except Exception as e:
            print(f"[ERROR] Failed to parse {f}: {e}")

    return parser.tree.root


def print_tree(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{node.report()}")
    for child in node.children:
        print_tree(child, indent + 1)


if __name__ == "__main__":
    tex_dir = "../demo-data/2212-11476/tex/2212.11476v1"
    tree_root = build_document_tree(tex_dir)

    if tree_root:
        print("\n--- Document Hierarchy Tree ---")
        print_tree(tree_root)