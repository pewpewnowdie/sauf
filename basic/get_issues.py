import requests

endpoint = "http://localhost:8000/api/issues"
response = requests.get(endpoint, json={'query' : 'status not in ("Open", "Closed", "InProgress") and assignee = "1" ORDER BY priority DESC'})
if response.status_code == 200:
    print(response.text)
else:
    print(response.text)