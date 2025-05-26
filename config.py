import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_ADMIN_ID = 8393893      # dedicated Intercom teammate used by the bot
DELAY_MIN_SECONDS = 0      # minimum delay after the LAST user message
DELAY_MAX_SECONDS = 1     # maximum delay after the LAST user message

# Intercom API
INTERCOM_ACCESS_TOKEN = os.getenv('INTERCOM_TOKEN')
INTERCOM_WEBHOOK_SECRET = os.getenv('INTERCOM_WEBHOOK_SECRET')

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4.1')

# MongoDB
DASHBOARD_DB_URI = os.getenv('DASHBOARD_DB_URI')

# Flask
FLASK_PORT = int(os.getenv('PORT', 5003))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'

# Testing
TESTING = True  # Set to False to reply for everyone
TEST_EMAIL = 'kmswong@gmail.com' 