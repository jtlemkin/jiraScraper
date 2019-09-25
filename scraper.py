import requests
from dateutil.parser import parse
from datetime import timedelta

def parseIssuesToCSV(url):
    f = open('jira_data.csv')
    print("id,severity,days_to_close,num_comments,num_commenters\n")

    i = 1
    while(True):
        resp = requests.get(url + str(i))

        if resp.status_code != 200:
            break

        priority = getPriority(resp.json())
        timeToFix = getTimeToFix(resp.json())
        numberOfComments = getNumberOfComments(resp.json())
        numberOfCommenters = getNumberOfCommenters(resp.json())

        print("{},{},{},{},{}\n".format(i, priority, timeToFix, numberOfComments, numberOfCommenters))

        i += 1

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