import requests

url = "http://127.0.0.1:8000/api/sync-stock/"
# event options restock,sync
data = {
    "machine_id": 7,
    "event": "sync",
    "stock": [
        {"slot": "a2", "product_id": 1, "quantity": 1},
        {"slot": "a1", "product_id": 2, "quantity": 1}
    ]
}

response = requests.post(url, json=data)

print(response.json())