import json
import pprint
from pathlib import Path
import csv
from collections import defaultdict
import sys

gcp_projects_dir = 'gcp_project'
count_projects_dir = 'count_project'

l = {}

with open('gcp_intersections_2230.csv') as f:

    intersections = defaultdict(list)
    for row in csv.DictReader(f):
        l[row['intersection']] = row['intersection']
   
print(json.dumps(l, indent=4))