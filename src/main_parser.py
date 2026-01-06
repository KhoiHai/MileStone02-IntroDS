import os
from parser.Publication_Parser import Publication_Parser

dataset_path = "../demo-data"
output_path = "../output"
os.makedirs(output_path, exist_ok=True)

# duyệt các publication
for pub_folder in os.listdir(dataset_path):
    pub_path = os.path.join(dataset_path, pub_folder)
    if not os.path.isdir(pub_path):
        continue

    print(f"\n=== Processing publication {pub_folder} ===")
    parser = Publication_Parser(pub_id=pub_folder, pub_path=pub_path)
    parser.parse_dataset()  # build trees, merge, extract refs

    # xuất graph và bib
    json_file = os.path.join(output_path, f"{pub_folder}_graph.json")
    bib_file = os.path.join(output_path, f"{pub_folder}_refs.bib")
    parser.export_json(json_file)
    parser.export_bib(bib_file)
