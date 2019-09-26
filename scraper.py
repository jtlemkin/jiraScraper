import requests
from dateutil.parser import parse
from datetime import timedelta
import os
import json


class IssueNotExistingError(Exception):
    """Raised when the issue does not exist in Jira"""
    pass


def getJiraJSON(url):
    resp = requests.get(url)

    if resp.status_code != 200:
        raise IssueNotExistingError

    #print(json.dumps(resp.json(), indent=4))

    return resp.json()


def writeIssueToFile(file, url, i):
    try:
        jiraJson = getJiraJSON(url + str(i))
    except IssueNotExistingError:
        raise

    print(i)

    priority = getPriority(jiraJson)
    timeToFix = getTimeToFix(jiraJson)
    numberOfComments = getNumberOfComments(jiraJson)
    numberOfCommenters = getNumberOfCommenters(jiraJson)

    file.write("{0},{1},{2:0.3f},{3},{4}\n".format(i, priority, timeToFix, numberOfComments, numberOfCommenters))


def getPriority(respJson):
    return respJson["fields"]["priority"]["name"]


def getTimeToFix(respJson):
    if respJson["fields"]["status"]["name"] == "Resolved":
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
    base_url = "https://issues.apache.org/jira/rest/api/latest/issue/"

    os.makedirs(project, exist_ok=True)

    fname = project + "/jira_data.csv"

    with open(fname, "a+") as f:
        #this isn't a good method but shouldn't be too much of an issue because the file shouldn't get too large
        def get_start():
            try:
                with open(project + "/resume.txt", "r") as t:
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
            line_no = start

            while True:
                try:
                    writeIssueToFile(f, project_url, line_no)
                except IssueNotExistingError:
                    print("issue does not exist, terminating")
                    return
                finally:
                    with open(project + "/resume.txt", "w+") as t:
                        t.write(str(line_no))

                line_no += 1

        write_all_issues_to_file()


scrape("ACCUMULO")

