import requests

url = "http://127.0.0.1:8000/api/sync-stock/"
data = {
    "machine_id": 7,
    "event": "sync",
    "stock": [
        {"slot": "a2", "product_id": 1, "quantity": 1, "sold": 5},
        {"slot": "a1", "product_id": 2, "quantity": 1, "sold": 5}
    ]
}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("Response Headers:", response.headers)

# Safely parse JSON if possible
try:
    json_data = response.json()
    print("Response JSON:", json_data)
except requests.exceptions.JSONDecodeError:
    print("Response is not JSON. Possibly empty or non-JSON response.")
import requests

url = "https://api.open-meteo.com/v1/forecast?latitude=37.98&longitude=23.81&current_weather=true"

response = requests.get(url)
data = response.json()
temp = data["current_weather"]["temperature"]
code = data["current_weather"]["weathercode"]
print(temp)
print(code)

#-_- test ground ===============================


