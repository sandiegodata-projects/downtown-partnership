import json
import pprint
from pathlib import Path

gcp_projects_dir = 'gcp_project'

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

    for url in urls:
        gcp_t['_via_img_metadata'][url] = mk_file_entry(url)

    return name, gcp_t

for up in Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/Annotations/URL Sets').glob('*'):
    try:
        name, d = update_project(up, Path('gcp_project_template.json'))
    except ValueError:
        print("ERROR: ", up)

    with Path(gcp_projects_dir).joinpath(name+'.json').open('w') as f:
        json.dump(d, f)

for up in Path('/Users/eric/Google Sync/sandiegodata.org/Projects/Downtown Partnership Homeless/Annotations/URL Sets').glob('*'):
    try:
        name, d = update_project(up, Path('homeless_projects.json'))
    except ValueError:
        print("ERROR: ", up)

    with Path(gcp_projects_dir).joinpath(name+'.json').open('w') as f:
        json.dump(d, f)
