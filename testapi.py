import requests

url = "http://localhost:8000/run"
payload = {"task": "Count the number of Wednesdays in /data/dates.txt and write the result to /data/wednesday-count.txt"}
response = requests.post(url, json=payload)
print(response.json())
