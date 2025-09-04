import requests

endpoint = "http://localhost:8000/api/projects"
params = {
    'query': 'start_date > "2025-09-10"'
}
response = requests.get(endpoint, params)
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)