import json
import requests
from dateutil.parser import parse
from datetime import timedelta

def parseIssuesToCSV(url):
    resp = requests.get(url)

    if resp.status_code != 200:
        raise ApiError('GET /tasks/ {}'.format(resp.status_code))

    #print(json.dumps(resp.json(), indent=4))
    priority = getPriority(resp.json())
    print(priority)

    timeToFix = getTimeToFix(resp.json())
    print(timeToFix)

def getPriority(respJson):
    return respJson["fields"]["priority"]["name"]

def getTimeToFix(respJson):
    resolutionDate = parse(respJson["fields"]["resolutiondate"])
    creationDate = parse(respJson["fields"]["created"])

    timeToFix = resolutionDate - creationDate
    timeToFixInDays = timeToFix / timedelta(days=1)

    return timeToFixInDays

url = "https://issues.apache.org/jira/rest/api/latest/issue/ACCUMULO-1?"
parseIssuesToCSV(url)