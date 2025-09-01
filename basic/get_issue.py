import requests

endpoint = "http://localhost:8000/api/issues"
response = requests.get(endpoint, json={'project' : ''})
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)