import requests
import json

url = "http://localhost:5000/routeplanning/plan_route"
payload = {
    "start_node": 2903,
    "end_node": 1104,
    "num_ants": 20,
    "max_iter": 50
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=4))

# python test_routing.py