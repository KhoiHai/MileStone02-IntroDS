import os
import re

INPUT_RE = re.compile(r'\\(?:input|include)\{([^}]+)\}')
DOC_RE = re.compile(r'\\documentclass')


# Function to determine the main tex file
def find_main_tex(tex_dir):
    for root, _, files in os.walk(tex_dir):
        for f in files:
            if f.endswith(".tex"):
                path = os.path.join(root, f)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as fp:
                        if DOC_RE.search(fp.read()):
                            return path
                except:
                    pass
    raise RuntimeError("No main tex file found")

# Resolve tex path
def resolve_tex_path(base_file, inc):
    if not inc.endswith(".tex"):
        inc += ".tex"
    return os.path.normpath(os.path.join(os.path.dirname(base_file), inc))

# Using DFS to collect tex files
def dfs_collect(main_tex):
    visited = set()
    ordered_files = []

    def dfs(tex_file):
        if tex_file in visited:
            return
        if not os.path.exists(tex_file):
            return

        visited.add(tex_file)
        ordered_files.append(tex_file)  

        try:
            with open(tex_file, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            return

        for inc in INPUT_RE.findall(content):
            dfs(resolve_tex_path(tex_file, inc))

    dfs(main_tex)
    return ordered_files

# The entire pipeline to collect tex files
def collect_tex_file(tex_dir):
    try:
        main_tex = find_main_tex(tex_dir)
    except RuntimeError as e:
        print(f"[WARN] {e} in {tex_dir}")
        return None, []

    used_files = dfs_collect(main_tex)

    if not used_files:
        print(f"[WARN] No tex files collected from {main_tex}")
        return main_tex, []

    return main_tex, sorted(used_files)

if __name__ == "__main__":
    tex_dir = "../../demo-data/2212-11482/tex/2212.11482v1"
    main_tex, used_files = collect_tex_file(tex_dir)

    print("Main file:", main_tex)
    print("Used tex files:")
    for f in used_files:
        print("-", f)