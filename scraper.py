import json
import requests
from dateutil.parser import parse
from datetime import timedelta

url = "https://issues.apache.org/jira/rest/api/latest/issue/ACCUMULO-1?"
resp = requests.get(url)

if resp.status_code != 200:
    raise ApiError('GET /tasks/ {}'.format(resp.status_code))

#print(json.dumps(resp.json(), indent=4))
#print('{}'.format(resp.json()["fields"]["priority"]["name"]))

resolutionDate = parse(resp.json()["fields"]["resolutiondate"])
print('{}'.format(resolutionDate))

creationDate = parse(resp.json()["fields"]["created"])
print('{}'.format(creationDate))

timeToFix = resolutionDate - creationDate
timeToFixInDays = timeToFix / timedelta(days=1)
print(timeToFixInDays)