import requests
import json

API_KEY = "a6a13808-747c-4411-8f6b-731a3f6f171a"

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