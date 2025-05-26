import os
import requests
import json
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
INTERCOM_ACCESS_TOKEN = os.getenv("INTERCOM_TOKEN")
headers = {
    "Authorization": f"Bearer {INTERCOM_ACCESS_TOKEN}",
    "Accept": "application/json"
}

def html_to_text(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

with open("conversations.json") as f:
    conversations = json.load(f)

all_convs = []

for i, conv in enumerate(conversations):
    conv_id = conv["id"]
    url = f"https://api.intercom.io/conversations/{conv_id}"
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        print(f"Failed to fetch conversation {conv_id}: {resp.status_code}")
        continue
    data = resp.json()
    messages = []
    # Add initial message
    source = data.get("source", {})
    role = "user" if source.get("author", {}).get("type") == "user" else "admin"
    text = html_to_text(source.get("body", ""))
    if text:
        messages.append({"role": role, "text": text})
    # Fetch all conversation parts (handle pagination)
    parts = data.get("conversation_parts", {}).get("conversation_parts", [])
    next_page = data.get("conversation_parts", {}).get("pages", {}).get("next")
    while next_page:
        parts_url = f"https://api.intercom.io/conversations/{conv_id}/parts"
        resp_parts = requests.get(parts_url, headers=headers, params=next_page)
        if not resp_parts.ok:
            print(f"Failed to fetch parts for conversation {conv_id}: {resp_parts.status_code}")
            break
        parts_data = resp_parts.json()
        parts.extend(parts_data.get("conversation_parts", []))
        next_page = parts_data.get("pages", {}).get("next")
        time.sleep(0.2)
    # Add all parts as messages
    for part in parts:
        part_role = part.get("author", {}).get("type")
        if part_role not in ["user", "admin"]:
            continue
        part_text = html_to_text(part.get("body", ""))
        if part_text:
            messages.append({"role": part_role, "text": part_text})
    if messages:
        all_convs.append({"id": conv_id, "messages": messages})
    if (i+1) % 10 == 0:
        print(f"Processed {i+1}/{len(conversations)} conversations...")
    time.sleep(0.2)

with open("conversations_for_llm.json", "w") as f:
    json.dump(all_convs, f, indent=2)
print(f"Extracted {len(all_convs)} conversations for LLM training.") 