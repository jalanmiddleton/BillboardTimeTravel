import csv

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

file_csv = "./py/data/songlinks.csv"
lines = []
with open(file_csv, "r") as infile:
    for line in infile.readlines():
        if line.strip():
            lines.append(line.strip())

with open(file_csv, "w") as outfile:
    for line in lines:
        outfile.write(line + "\n")