import requests

endpoint = "http://localhost:8000/api/issues"
params = {
    'query': 'project = IUG'
}
response = requests.get(endpoint, params)
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)