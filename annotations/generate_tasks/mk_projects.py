import json
import pprint
from pathlib import Path
import csv
from collections import defaultdict
import sys

gcp_projects_dir = 'gcp_project'
count_projects_dir = 'count_project'

##
## Load all of the intersection names, organized so they can be applied
## individually to project files
with open('gcp_intersections_2230.csv') as f:
    intersections = defaultdict(dict)
    for row in csv.DictReader(f):
        intersections[row['neighborhood']][row['intersection']] = row['intersection']
   
intersections['east_villiage'] = intersections['east_village']     
intersections['east_villiage_south'] = intersections['east_village']

## Load the example files entries. 

examples = {}
with open('gcp_examples.json') as f:
    e = json.load(f)
    for k, v in e["_via_img_metadata"].items():
    
        n = v["file_attributes"]["neighborhood"]
        v["file_attributes"] = {}
        examples[n] = v
    
def mk_file_entry(url):
    return {'file_attributes': {},
     'filename': url,
     'regions': [],
     'size': -1}

def update_project(urls_path, template_path):
    neighborhood, year = urls_path.stem.split('-')
    grp, *_ = template_path.stem.split('_')

    with template_path.open() as f:
        gcp_t = json.load(f)

    with urls_path.open() as f:
        urls = [e.strip() for e in f]

    name = f"{neighborhood}-{grp}-{year}"

    gcp_t.get('_via_settings',{}).get('project',{})['name'] = name

    if grp == 'gcp':
      
        gcp_t['_via_img_metadata']['example'] = examples[neighborhood]

    for url in urls:
        gcp_t['_via_img_metadata'][url] = mk_file_entry(url)


    try:
        intr = gcp_t["_via_attributes"]["region"]["Intersection"]
    except KeyError:
        # The homeless_project_template don't have these attributed
        return name, gcp_t

    intr["options"]  = intersections[neighborhood]

    return name, gcp_t


# Create the projects from the templates

for up in Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/Annotations/URL Sets').glob('*'):
    try:
        name, d = update_project(up, Path('gcp_project_template.json'))
    except ValueError:
        print("ERROR: ", up)

    with Path(gcp_projects_dir).joinpath(name+'.json').open('w') as f:
        json.dump(d, f, indent=4)

for up in Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/Annotations/URL Sets').glob('*'):
    try:
        name, d = update_project(up, Path('homeless_project_template.json'))
    except ValueError:
        print("ERROR: ", up)

    with Path(count_projects_dir).joinpath(name+'.json').open('w') as f:
        json.dump(d, f, indent=4)
