import requests
import json

API_KEY = ""

url = "https://eventregistry.org/api/v1/article/getArticles"

payload = {
    "apiKey": API_KEY,
    "query": {
        "$query": {
            "$and": [
                {
                    "keyword": "Apple"
                }
            ]
        }
    },
    "resultType": "articles",
    "articlesSortBy": "date",
    "articlesCount": 5
}

try:
    response = requests.post(url, json=payload)

    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=4))

except Exception as e:
    print(f"Error: {e}")