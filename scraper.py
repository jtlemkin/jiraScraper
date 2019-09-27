import requests
from dateutil.parser import parse
from datetime import timedelta
import os
import json
import sys


class IssueNotExistingError(Exception):
    """Raised when the issue does not exist in Jira"""
    pass


def get_jira_json(project, url, i):
    try:
        f = open("data/" + project + "/json/" + str(i) + "_issue.json", "r")
    except FileNotFoundError:
        issue_url = url + str(i)
        resp = requests.get(issue_url)

        if resp.status_code != 200:
            raise IssueNotExistingError

        # print(json.dumps(resp.json(), indent=4))

        jira_json = resp.json()

        with open("data/" + project + "/json/" + str(i) + "_issue.json", "w+") as f:
            json.dump(jira_json, f)
    else:
        jira_json = json.load(f)
        f.close()

    return jira_json


def write_issue_to_file(file, project, url, i):
    try:
        jiraJson = get_jira_json(project, url, i)
    except IssueNotExistingError:
        raise

    print(project + " " + str(i))

    priority = getPriority(jiraJson)
    timeToFix = getTimeToFix(jiraJson)
    numberOfComments = getNumberOfComments(jiraJson)
    numberOfCommenters = getNumberOfCommenters(jiraJson)

    file.write("{0},{5},{1},{2:0.3f},{3},{4}\n".format(i, priority, timeToFix, numberOfComments, numberOfCommenters, project))


def getPriority(respJson):
    return respJson["fields"]["priority"]["name"]


def getTimeToFix(respJson):
    status = respJson["fields"]["status"]["name"]
    if status == "Closed" or status == "Resolved":
        resolutionDate = parse(respJson["fields"]["resolutiondate"])
        creationDate = parse(respJson["fields"]["created"])

        timeToFix = resolutionDate - creationDate
        timeToFixInDays = timeToFix / timedelta(days=1)

        return timeToFixInDays
    else:
        #-1 indicates that the issue has not been fixed
        return -1


def getNumberOfComments(respJson):
    comments = respJson["fields"]["comment"]["comments"]
    return len(comments)


def getNumberOfCommenters(respJson):
    authors = set()

    comments = respJson["fields"]["comment"]["comments"]
    for comment in comments:
        authors.add(comment["author"]["name"])

    return len(authors)


def scrape(project):
    print("PROCESSING " + project)

    base_url = "https://issues.apache.org/jira/rest/api/latest/issue/"

    os.makedirs("data/" + project + "/json", exist_ok=True)

    fname = "data/" + project + "/jira_data.csv"

    with open(fname, "a+") as f:
        #this isn't a good method but shouldn't be too much of an issue because the file shouldn't get too large
        def get_start():
            try:
                with open("data/" + project + "/resume.txt", "r") as t:
                    try:
                        start = int(t.readline())
                    except ValueError:
                        return 1

                return start
            except FileNotFoundError:
                return 1

        start = get_start()

        if start == 1:
            f.write("issue_id,project_name,severity,days_to_close,num_comments,num_commenters\n")

        project_url = base_url + project + "-"

        def write_all_issues_to_file():
            issue_no = start
            consecutive_missed = 0

            threshold_for_missed = 10

            while True:
                try:
                    consecutive_missed = 0
                    write_issue_to_file(f, project, project_url, issue_no)
                except IssueNotExistingError:
                    consecutive_missed += 1

                    if consecutive_missed < threshold_for_missed:
                        pass
                    else:
                        print("terminating at issue " + issue_no)
                        return
                finally:
                    with open("data/" + project + "/resume.txt", "w+") as t:
                        t.write(str(issue_no))

                issue_no += 1

        write_all_issues_to_file()

scrape("JCR")
scrape(sys.argv[1])

