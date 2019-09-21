import json
import requests
from dateutil.parser import parse
from datetime import timedelta
import csv

def parseIssuesToCSV(url):
    resp = requests.get(url)

    if resp.status_code != 200:
        raise ApiError('GET /tasks/ {}'.format(resp.status_code))

    #print(json.dumps(resp.json(), indent=4))

    priority = getPriority(resp.json())
    print(priority)

    timeToFix = getTimeToFix(resp.json())
    print(timeToFix)

    numberOfComments = getNumberOfComments(resp.json())
    print(numberOfComments)

    numberOfCommenters = getNumberOfCommenters(resp.json())
    print(numberOfCommenters)

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

url = "https://issues.apache.org/jira/rest/api/latest/issue/ACCUMULO-3?"
parseIssuesToCSV(url)