import requests
data = requests.get("https://fakestoreapi.com/products").json()
for p in data:
    print(p["title"], "-", p["category"], "-", p["price"])
