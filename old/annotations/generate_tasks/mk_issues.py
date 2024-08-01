from os import environ
import sys
from pathlib import Path
from github import Github
from github.GithubException import UnknownObjectException

def yield_issues(typ):
    from boto3 import client

    conn = client('s3')  # again assumes boto.cfg setup, assume AWS S3

    if typ == 'gcp':
        prj_name = 'gcp_project'
    else:
        prj_name = 'count_project'

    root_url = 'http://ds.civicknowledge.org/'
    o = conn.list_objects(Bucket='ds.civicknowledge.org', Prefix=f'/downtownsandiego.org/annotations/{prj_name}')

    for key in conn.list_objects(Bucket='ds.civicknowledge.org', Prefix=f'downtownsandiego.org/annotations/{prj_name}/')['Contents']:
        if key['Size']:
            p = Path(key['Key'])
            neighborhood, typ_, year = p.stem.split('-')
        
     
            url = root_url+key['Key']
        
            if typ == 'gcp':
                d = {
                    'title': f"GCP For {neighborhood.title()} Neighborhood, {year}",
                    'body': f"""Set Ground Control Points for the {neighborhood.title()} neighborhood, using this [VIA](http://www.robots.ox.ac.uk/~vgg/software/via/via.html) configuration file:

{url}
    
Follow [these instructions](https://docs.google.com/document/d/1Rh1EB405sHHgFKuIfyLE9JAA1VUPzOGa1_iUwfb8h6g/edit?usp=sharing) for placing the Ground Control Points. 
    """}
        
            else:
                d = {
                    'title': f"Homeless Counts For {neighborhood.title()} Neighborhood, {year}",
                    'body': f"""Geolocate homeless counts for the {neighborhood.title()} neighborhood, using this [VIA](http://www.robots.ox.ac.uk/~vgg/software/via/via.html) configuration file:

{url}
    
Follow [these instuctions](https://docs.google.com/document/d/1E_ZJXS3GjzxOPLRHuTBhde-jQrbn4uc7D57YGoXlyuo/edit?usp=sharing) for digitizing the homeless count maps with VIA. 
        """}
        
            yield typ, year, neighborhood, d
        else:
            print("No size", key)


# or using an access token
g = Github(environ['GITHUB_TOKEN'])

repo = g.get_repo("sandiegodata-projects/downtown-partnership")

def make_labels(typ):
    """Make labels for the issues"""

    for typ, year, neighborhood, issue in yield_issues(typ):
        try:
            label = repo.get_label(neighborhood)
        except UnknownObjectException:
            label = repo.create_label(neighborhood, color='389e56')

        try:
            label = repo.get_label(typ)
        except UnknownObjectException:
            label = repo.create_label(typ, color='389e56')

        try:
            label = repo.get_label(year)
        except UnknownObjectException:
            label = repo.create_label(year, color='389e56')


#make_labels('gcp')
#make_labels('counts')

def create_issues(typ):
    
    for typ, year, neighborhood, issue in yield_issues(typ):

        
        #print('!!!', neighborhood, typ, year)
        labels = [repo.get_label(neighborhood), repo.get_label(typ), repo.get_label(year)]
        
        extant =  repo.get_issues(state='open', labels=labels)
        
        if extant.totalCount == 0:
            r =repo.create_issue(**issue, labels=labels)
            print('CREATED ', issue['title'])
        else:
            print('EXISTS', issue['title'])
             
create_issues('gcp')
create_issues('counts')
    
sys.exit(0)