import os
import shutil
from parser.Publication_Parser import Publication_Parser

dataset_path = "../demo-data"

# Go through every publication folder
for pub_folder in os.listdir(dataset_path):
    pub_path = os.path.join(dataset_path, pub_folder)
    if not os.path.isdir(pub_path):
        continue

    print(f"\n=== Processing publication {pub_folder} ===")

    # Initialize parser
    parser = Publication_Parser(pub_id=pub_folder, pub_path=pub_path)
    parser.parse_dataset()  # build trees, merge, extract refs

    # Json và bib export
    json_file = os.path.join(pub_path, f"{pub_folder}_graph.json")
    bib_file = os.path.join(pub_path, f"{pub_folder}_refs.bib")
    parser.export_json(json_file)
    parser.export_bib(bib_file)
    print(f"Exported: {json_file} and {bib_file}")

    tex_path = os.path.join(pub_path, "tex")
    if os.path.exists(tex_path) and os.path.isdir(tex_path):
        shutil.rmtree(tex_path)
        print(f"Deleted folder: {tex_path}")
