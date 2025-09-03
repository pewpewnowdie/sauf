import requests

endpoint = "http://localhost:8000/api/projects"
response = requests.get(endpoint)
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)