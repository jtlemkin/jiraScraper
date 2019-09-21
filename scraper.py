import requests

url = "https://issues.apache.org/jira/rest/api/latest/issue/ACCUMULO-1"
resp = requests.get(url)

if resp.status_code != 200:
    raise ApiError('GET /tasks/ {}'.format(resp.status_code))

print(resp.json())