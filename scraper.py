import requests
from dateutil.parser import parse
from datetime import timedelta
import os
import json
import sys
import pygit2


class IssueNotExistingError(Exception):
    """Raised when the issue does not exist in Jira"""
    pass


def get_jira_json(project, url, i):
    json_file_path = "data/json/" + project + "/" + str(i) + "_issue.json"

    try:
        f = open(json_file_path, "r")
    except FileNotFoundError:
        issue_url = url + str(i)
        resp = requests.get(issue_url)

        if resp.status_code != 200:
            raise IssueNotExistingError

        # print(json.dumps(resp.json(), indent=4))

        jira_json = resp.json()

        with open(json_file_path, "w+") as f:
            json.dump(jira_json, f)
    else:
        jira_json = json.load(f)
        f.close()

    return jira_json


def get_issue_links(jira_json):
    json_issuelinks = jira_json["fields"]["issuelinks"]

    breaks = "NONE"
    is_broken_by = "NONE"

    # assumes only one link breaks link and is broken by link per issue
    for link in json_issuelinks:
        if "outwardIssue" in link and link["type"]["outward"] == "breaks":
            breaks = link["outwardIssue"]["key"]

        if "inwardIssue" in link and link["type"]["inward"] == "is broken by":
            is_broken_by = link["inwardIssue"]["key"]

    return breaks, is_broken_by


def get_type(jira_json):
    return jira_json["fields"]["issuetype"]["name"]


def write_issue_to_file(file, project, url, i):
    try:
        jira_json = get_jira_json(project, url, i)
    except IssueNotExistingError:
        raise

    bug_id = project + "-" + str(i)
    print(bug_id)

    issue_type = get_type(jira_json)
    priority = get_priority(jira_json)
    time_to_fix = get_time_to_fix(jira_json)
    number_of_comments = get_number_of_comments(jira_json)
    number_of_commenters = get_number_of_commenters(jira_json)
    breaks, is_broken_by = get_issue_links(jira_json)

    file.write("{0},{7},{1},{2:0.3f},{3},{4},{5},{6}\n".format(bug_id, priority, time_to_fix, number_of_comments,
                                                               number_of_commenters, breaks, is_broken_by, issue_type))


def get_priority(resp_json):
    return resp_json["fields"]["priority"]["name"]


def get_time_to_fix(resp_json):
    status = resp_json["fields"]["status"]["name"]
    if (status == "Closed" or status == "Resolved") and resp_json["fields"]["resolutiondate"]:
        resolution_date = parse(resp_json["fields"]["resolutiondate"])
        creation_date = parse(resp_json["fields"]["created"])

        time_to_fix = resolution_date - creation_date
        time_to_fix_in_days = time_to_fix / timedelta(days=1)

        return time_to_fix_in_days
    else:
        # -1 indicates that the issue has not been fixed
        return -1


def get_number_of_comments(resp_json):
    comments = resp_json["fields"]["comment"]["comments"]
    return len(comments)


def get_number_of_commenters(resp_json):
    authors = set()

    comments = resp_json["fields"]["comment"]["comments"]
    for comment in comments:
        authors.add(comment["author"]["name"])

    return len(authors)


def create_dirs(project):
    os.makedirs("data/json/" + project, exist_ok=True)
    os.makedirs("data/csvs/", exist_ok=True)
    os.makedirs("data/starts", exist_ok=True)


def scrape(project, task):
    print("PROCESSING " + project)

    base_url = "https://issues.apache.org/jira/rest/api/latest/issue/"

    create_dirs(project)

    fname = "data/csvs/" + project + ".csv"

    repo = pygit2.Repository("../apache/" + project.lower())

    with open(fname, "a+") as f:
        # this isn't a good method but shouldn't be too much of an issue because the file shouldn't get too large
        def get_start():
            try:
                with open("data/starts/" + project + "_start.txt", "r") as t:
                    try:
                        start = int(t.readline())
                    except ValueError:
                        return 1

                return start
            except FileNotFoundError:
                return 1

        start = get_start()

        if start == 1:
            f.write("bug_id,issue_type,severity,days_to_close,num_comments,num_commenters,breaks,is_broken_by\n")

        project_url = base_url + project + "-"

        def write_all_issues_to_file():
            issue_no = start
            consecutive_missed = 0

            threshold_for_missed = 20

            while True:
                try:
                    #task(f, project, project_url, issue_no)
                    task(f, project, issue_no, repo)
                except IssueNotExistingError:
                    consecutive_missed += 1

                    if consecutive_missed < threshold_for_missed:
                        pass
                    else:
                        print("Terminating at issue " + str(issue_no))
                        return
                else:
                    consecutive_missed = 0
                finally:
                    with open("data/starts/" + project + "_start.txt", "w+") as t:
                        t.write(str(issue_no))

                issue_no += 1

        write_all_issues_to_file()


def get_issue_commits(repo, project, issue_no):
    last = repo[repo.head.target]

    project_id = project + "-" + str(issue_no) + " "

    commits = []

    found_match = False
    num_commits_since_match = 0

    for commit in repo.walk(last.id, pygit2.GIT_SORT_TIME):
        if project_id in commit.message:
            commits.append(commit)

        # This makes the assumption that commits pertaining to the same issue are not too far away
        if found_match:
            num_commits_since_match += 1

        if num_commits_since_match > 100:
            break

    return commits


def write_issue_commits_to_file(f, project, issue_no, repo):
    commits = get_issue_commits(repo, project, issue_no)
    pass


#scrape(sys.argv[1], write_issue_to_file)
#TODO
#change this back!
#scrape("ACCUMULO", write_issue_commits_to_file)

repo = pygit2.Repository("../apache/" + "accumulo")

write_issue_commits_to_file(None, "ACCUMULO", 3580, repo)