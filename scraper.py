import requests
from dateutil.parser import parse
from datetime import timedelta

class IssueNotExistingError(Exception):
    """Raised when the issue does not exist in Jira"""
    pass

def getJiraJSON(url):
    resp = requests.get(url)

    if resp.status_code != 200:
        raise IssueNotExistingError

    return resp.json()

def writeIssueToFile(file, i):
    try:
        json = getJiraJSON(url + str(i))
    except IssueNotExistingError:
        raise

    priority = getPriority(json)
    timeToFix = getTimeToFix(json)
    numberOfComments = getNumberOfComments(json)
    numberOfCommenters = getNumberOfCommenters(json)

    print("{},{},{},{},{}\n".format(i, priority, timeToFix, numberOfComments, numberOfCommenters))

def writeAllIssuesToFile(file):
    i = 1
    while (True):
        try:
            writeIssueToFile(file, 5000)
        except IssueNotExistingError:
            return

        i += 1

def parseIssuesToCSV(url):
    f = open('jira_data.csv')
    print("id,severity,days_to_close,num_comments,num_commenters\n")

    #writeIssueToFile(f, 5000)
    writeAllIssuesToFile(f)

    f.close()

def getPriority(respJson):
    return respJson["fields"]["priority"]["name"]

def getTimeToFix(respJson):
    resolutionDate = parse(respJson["fields"]["resolutiondate"])
    creationDate = parse(respJson["fields"]["created"])

    timeToFix = resolutionDate - creationDate
    timeToFixInDays = timeToFix / timedelta(days=1)

    return timeToFixInDays

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