import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_ADMIN_ID = 8393893      # dedicated Intercom teammate used by the bot
BOT_ASSISTANT_NAME = "katie"  # name for AI assistant triggered by admin notes
DELAY_MIN_SECONDS = 20      # minimum delay after the LAST user message
DELAY_MAX_SECONDS = 50      # maximum delay after the LAST user message

# Intercom API
INTERCOM_ACCESS_TOKEN = os.getenv('INTERCOM_TOKEN')
INTERCOM_WEBHOOK_SECRET = os.getenv('INTERCOM_WEBHOOK_SECRET')

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-5-chat')

# AI Model Configuration
STRONG_REASONING = 'o1'
NORMAL = 'gpt-5-chat'
FAST = 'gpt4omini'
NANO = 'gpt-5-nano'

# MongoDB
DASHBOARD_DB_URI = os.getenv('DASHBOARD_DB_URI')
APP_DB_URI = os.getenv('APP_DB_URI')

# Flask
FLASK_PORT = int(os.getenv('PORT', 5003))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'

# Testing
TESTING = True  # Set to False to reply for everyone
TEST_EMAIL = 'kmswong@gmail.com' 