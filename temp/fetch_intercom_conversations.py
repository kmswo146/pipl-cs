import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
INTERCOM_ACCESS_TOKEN = os.getenv("INTERCOM_TOKEN")
headers = {
    "Authorization": f"Bearer {INTERCOM_ACCESS_TOKEN}",
    "Accept": "application/json"
}

six_months_ago = int((datetime.utcnow() - timedelta(days=90)).timestamp())
conversations = []
url = "https://api.intercom.io/conversations"
params = {"per_page": 60}

while url:
    print(f"Fetching: {url} with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        print(f"Failed to fetch conversations: {response.status_code} {response.text}")
        break
    data = response.json()
    page_convs = data.get("conversations", [])
    print(f"Conversations in this page: {len(page_convs)}")
    for conv in page_convs:
        if conv.get("created_at", 0) >= six_months_ago:
            conversations.append(conv)
    next_page = data.get("pages", {}).get("next")
    print(f"Next page: {next_page}")
    if isinstance(next_page, dict) and next_page:
        params = next_page
    else:
        break

with open("conversations.json", "w") as f:
    json.dump(conversations, f, indent=2)
print(f"Fetched {len(conversations)} conversations from the last 6 months.") 