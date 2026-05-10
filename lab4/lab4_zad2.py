!pip install pymongo mongomock requests

import requests
import mongomock
from pprint import pprint

client = mongomock.MongoClient()

db = client["crypto_db"]
collection = db["networks"]


url = "https://api.geckoterminal.com/api/v2/networks"

response = requests.get(url)
data = response.json()["data"]

documents = []

for network in data:
    attr = network["attributes"]

    doc = {
        "network_id": network["id"],
        "name": attr.get("name"),
        "coingecko_asset_platform_id": attr.get("coingecko_asset_platform_id")
    }

    documents.append(doc)

collection.insert_many(documents)

print(f"Dodano {len(documents)} dokumentów.")

pipeline = [
    {
        "$group": {
            "_id": "$coingecko_asset_platform_id",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"count": -1}
    }
]

result = collection.aggregate(pipeline)

print("Liczba sieci per typ:\n")

for item in result:
    pprint(item)