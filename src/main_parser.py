import os
import shutil
from parser.Publication_Parser import Publication_Parser

dataset_path = "../data"

all_pub_success_rates = []

# Go through every publication folder
for pub_folder in os.listdir(dataset_path):
    pub_path = os.path.join(dataset_path, pub_folder)
    if not os.path.isdir(pub_path):
        continue

    print(f"\n=== Processing publication {pub_folder} ===")

    # Initialize parser
    parser = Publication_Parser(pub_id=pub_folder, pub_path=pub_path)
    parser.parse_dataset()  # build trees, merge, extract refs

    # Success rate of publication
    all_pub_success_rates.append(parser.success_rate)
    print(f"[INFO] Publication '{pub_folder}' parsing success rate: {parser.success_rate:.2f}%")

    # Export JSON và bib
    json_file = os.path.join(pub_path, f"hierarchy.json")
    bib_file = os.path.join(pub_path, f"refs.bib")
    parser.export_json(json_file)
    parser.export_bib(bib_file)
    print(f"Exported: {json_file} and {bib_file}")

    # Delete folder tex
    tex_path = os.path.join(pub_path, "tex")
    if os.path.exists(tex_path) and os.path.isdir(tex_path):
        shutil.rmtree(tex_path)
        print(f"Deleted folder: {tex_path}")

# Calculate success rate
if all_pub_success_rates:
    overall_rate = sum(all_pub_success_rates) / len(all_pub_success_rates)
    print(f"\n=== Overall parsing success rate across all publications: {overall_rate:.2f}% ===")
else:
    print("\n=== No publications were processed. ===")
