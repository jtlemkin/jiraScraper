import requests
from dateutil.parser import parse
from datetime import timedelta
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

    priority = getPriority(jiraJson)
    timeToFix = getTimeToFix(jiraJson)
    numberOfComments = getNumberOfComments(jiraJson)
    numberOfCommenters = getNumberOfCommenters(jiraJson)

    print("{0},{1},{2:0.3f},{3},{4}\n".format(i, priority, timeToFix, numberOfComments, numberOfCommenters))

def writeAllIssuesToFile(file, base_url):
    i = 1
    while (True):
        try:
            writeIssueToFile(file, base_url, i)
        except IssueNotExistingError:
            return

        i += 1

def parseIssuesToCSV(base_url):
    f = open('jira_data.csv')
    print("id,severity,days_to_close,num_comments,num_commenters\n")

    writeAllIssuesToFile(f, base_url)

    f.close()

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

url = "https://issues.apache.org/jira/rest/api/latest/issue/ACCUMULO-"
parseIssuesToCSV(url)