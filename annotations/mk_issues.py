from os import environ

from github import Github

#
# or using an access token
g = Github(environ['GITHUB_TOKEN'])

repo = g.get_repo("sandiegodata-projects/downtown-partnership")
print(repo)

open_issues = repo.get_issues(state='closed')
for issue in open_issues:
    print(issue.comments)

    for c in repo.get_comments():
        print(c)


    print(repo.get_comment(0))

#repo.create_issue(title="This is a new issue", body="""GCP Project
#Use this [GCP Input file](http://ds.civicknowledge.org/downtownsandiego.org/annotations/gcp_project/columbia-gcp-2015.json)""")
