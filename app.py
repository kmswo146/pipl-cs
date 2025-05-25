import os
import hmac
import hashlib
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
import requests
import openai

# Load environment variables
load_dotenv()

INTERCOM_ACCESS_TOKEN = os.getenv('INTERCOM_TOKEN')
INTERCOM_WEBHOOK_SECRET = os.getenv('INTERCOM_WEBHOOK_SECRET')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4')
BOT_NAME = os.getenv('BOT_NAME', 'AI Assistant')
TESTING = True  # Set to False to reply for everyone
ADMIN_ID = "6876491"

# Set up Azure OpenAI client
client = openai.AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

app = Flask(__name__)

@app.route('/webhook/', methods=['POST'])
def webhook():
    data = request.json
    print('Received Intercom webhook payload:')
    print(data)
    # Extract email
    try:
        email = data['data']['item']['source']['author']['email']
    except Exception as e:
        print('Could not extract email:', e)
        email = None
    print(f"TESTING flag: {TESTING}")
    print(f"Extracted email: {email}")
    should_reply = False
    if TESTING:
        if email == 'kmswong@gmail.com':
            should_reply = True
    else:
        should_reply = True
    if should_reply:
        print("Triggering Intercom auto-reply...")
        conversation_id = data['data']['item']['id']
        reply_body = '<p>Test reply with image:</p><img src="https://app.pipl.ai/v2/images/logo.png" alt="logo" style="max-width:200px;" />'
        send_intercom_reply(conversation_id, reply_body)
    else:
        print("Auto-reply not triggered (check TESTING flag and email match).")
    return jsonify({'status': 'ok'})

def get_ai_reply(user_message):
    # You may want to adjust the deployment/model name as per your Azure setup
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": f"You are {BOT_NAME}, an AI assistant."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content.strip()

def send_intercom_reply(conversation_id, message):
    url = f'https://api.intercom.io/conversations/{conversation_id}/reply'
    headers = {
        'Authorization': f'Bearer {INTERCOM_ACCESS_TOKEN}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    print('DEBUG: Using Intercom access token:', INTERCOM_ACCESS_TOKEN)  # REMOVE AFTER DEBUGGING
    print('DEBUG: Headers sent to Intercom:', headers)  # REMOVE AFTER DEBUGGING
    payload = {
        "type": "admin",
        "admin_id": ADMIN_ID,
        "message_type": "comment",
        "body": message
    }
    response = requests.post(url, headers=headers, json=payload)
    print('Intercom API response:', response.status_code, response.text)
    if not response.ok:
        print(f"Failed to send reply: {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5003)), debug=os.getenv('FLASK_DEBUG', 'False') == 'True') 