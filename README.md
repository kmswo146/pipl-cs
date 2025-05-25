# Intercom AI Bot

A robust AI-powered customer support bot for Intercom with intelligent conversation management and human handoff capabilities.

## Architecture

This bot follows a clean separation of concerns with two main components:

### 1. Webhook Server (`app/webhook.py`)
- Receives Intercom webhooks instantly
- Updates conversation state in MongoDB
- Handles human admin takeover logic
- Returns `200 OK` immediately (no heavy processing)

### 2. Worker Process (`worker/worker.py`)
- Scans for pending conversations every 10 seconds
- Processes conversations after a configurable delay (60s default)
- Generates intelligent replies using AI
- Sends replies via Intercom API

## Key Features

### Smart Human Handoff
- **Bot Pause**: When a human admin replies, the bot automatically pauses for that conversation
- **Auto Resume**: Bot resumes when conversation is closed and user sends new message
- **Testing Mode**: Only responds to specific test email during development

### Intelligent Reply Engine
- **Intent Classification**: Categorizes user messages (password reset, account queries, general support)
- **FAQ Integration**: Serves canned responses from MongoDB for common questions
- **LLM Fallback**: Uses Azure OpenAI for complex queries
- **Context Awareness**: Maintains conversation history for better responses

### Robust State Management
- **MongoDB Integration**: Tracks conversation state, timing, and bot status
- **Delay Logic**: Waits 60 seconds after last user message before replying
- **Conflict Prevention**: Prevents bot from interfering with human agents

## File Structure

```
pv_bot/
├── config.py              # Configuration and environment variables
├── db.py                  # MongoDB helper functions
├── requirements.txt       # Python dependencies
├── start_webhook.py       # Webhook server startup script
├── app/
│   └── webhook.py         # Flask webhook handlers
└── worker/
    ├── worker.py          # Main worker process
    ├── intercom_api.py    # Intercom API wrapper
    └── reply_engine.py    # AI reply generation
```

## Configuration

Set these environment variables in your `.env` file:

```bash
# Intercom
INTERCOM_TOKEN=your_intercom_access_token

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
DEFAULT_MODEL=gpt-4

# MongoDB
DASHBOARD_DB_URI=your_mongodb_connection_string

# Flask
PORT=5003
FLASK_DEBUG=False
```

## MongoDB Schema

### `intercom_conversations` Collection
```json
{
  "_id": "215469136295889",           // conversation_id
  "user_id": "655cb0c58ec3458aee4e844f",
  "last_user_ts": "2025-01-25T12:00:00Z",
  "last_bot_ts": "2025-01-25T12:01:00Z",
  "pending_reply": true,
  "bot_paused": false,
  "awaiting_clarification": false
}
```

### `qa_entries` Collection
```json
{
  "_id": ObjectId("6832d2d44284c30bb33e46a5"),
  "question": "how to reset password",
  "answer": "<p>Click here, then click here</p><img src='...'/>",
  "createdAt": "2025-01-25T08:20:36.132Z",
  "updatedAt": "2025-01-25T08:20:36.132Z"
}
```

## Usage

### 1. Start the Webhook Server
```bash
python start_webhook.py
```

### 2. Start the Worker Process
```bash
python worker/worker.py
```

### 3. Configure Intercom Webhooks
Point your Intercom webhooks to: `https://your-domain.com/webhook/`

Subscribe to these topics:
- `conversation.user.created`
- `conversation.user.replied`
- `conversation.admin.replied`
- `conversation.admin.closed`

## Webhook Flow

| Topic | Action |
|-------|--------|
| `conversation.user.created`<br>`conversation.user.replied` | Upsert conversation doc:<br>`pending_reply: true`<br>`last_user_ts: now()` |
| `conversation.admin.replied` | If admin ≠ BOT_ADMIN_ID:<br>`bot_paused: true`<br>`pending_reply: false` |
| `conversation.admin.closed` | Reset all flags:<br>`bot_paused: false`<br>`pending_reply: false` |

## Worker Logic

1. **Query**: Find conversations where:
   - `pending_reply: true`
   - `bot_paused: false`
   - `last_user_ts` > 60 seconds ago

2. **Process**: For each conversation:
   - Fetch full history from Intercom
   - Generate AI reply
   - Send reply via Intercom API
   - Update conversation state

3. **Repeat**: Every 10 seconds

## Constants

- `BOT_ADMIN_ID = 8393893` - Dedicated Intercom admin account for bot
- `DELAY_SECONDS = 60` - Wait time after last user message
- Testing mode only responds to `kmswong@gmail.com`

## Human Override

When any human admin (ID ≠ 8393893) replies to a conversation:
- Bot immediately pauses (`bot_paused: true`)
- No more auto-replies until conversation is closed
- Fresh cycle starts when user messages after close

This ensures seamless handoff between bot and human agents without conflicts. 