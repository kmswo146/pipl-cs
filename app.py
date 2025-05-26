from flask import Flask, request, jsonify
import config
import db

app = Flask(__name__)

@app.route('/webhook/', methods=['POST'])
def webhook():
    data = request.json
    topic = data.get('topic', 'unknown')
    
    print(f'Received Intercom webhook - Topic: {topic}')
    
    try:
        if topic in ['conversation.user.created', 'conversation.user.replied']:
            handle_user_message(data)
        elif topic == 'conversation.admin.replied':
            handle_admin_reply(data)
        elif topic == 'conversation.admin.closed':
            handle_conversation_closed(data)
        else:
            print(f'Unhandled topic: {topic}')
            
    except Exception as e:
        print(f'Error processing webhook: {e}')
        
    return jsonify({'status': 'ok'})

def handle_user_message(data):
    """Handle user created/replied events"""
    try:
        conversation_id = data['data']['item']['id']
        user_id = data['data']['item']['source']['author']['id']
        email = data['data']['item']['source']['author'].get('email', '')
        
        print(f'DEBUG: conversation_id={conversation_id}, user_id={user_id}, email="{email}"')
        print(f'User message in conversation {conversation_id} from {email}')
        
        # NOTE: Testing flag is now handled in reply_engine for step 2+
        # Steps 0-1 will run for all users regardless of testing flag
        print(f'Processing conversation (Steps 0-1 will run for all users, Step 2+ respects testing flag)')
        
        # Check if bot is paused for this conversation
        existing_conv = db.intercom_conversations.find_one({"conversation_id": conversation_id})
        if existing_conv and existing_conv.get('bot_paused', False):
            print(f'Bot is paused for conversation {conversation_id} - ignoring user message')
            return
        
        # Upsert conversation document
        db.upsert_conversation(conversation_id, user_id, email)
        print(f'Upserted conversation {conversation_id} from {email} - pending_reply: True')
        
    except Exception as e:
        print(f'Error handling user message: {e}')

def handle_admin_reply(data):
    """Handle admin reply events"""
    try:
        conversation_id = data['data']['item']['id']
        admin_id = data['data']['item']['conversation_parts']['conversation_parts'][0]['author']['id']
        
        print(f'Admin reply in conversation {conversation_id} from admin {admin_id}')
        
        # If admin is NOT the bot, pause the bot
        if str(admin_id) != str(config.BOT_ADMIN_ID):
            db.pause_bot_for_conversation(conversation_id)
            print(f'Human admin {admin_id} replied - bot paused for conversation {conversation_id}')
        else:
            print(f'Bot admin {admin_id} replied - no action needed')
            
    except Exception as e:
        print(f'Error handling admin reply: {e}')

def handle_conversation_closed(data):
    """Handle conversation closed events"""
    try:
        conversation_id = data['data']['item']['id']
        
        print(f'Conversation {conversation_id} closed - resetting flags')
        db.reset_conversation_flags(conversation_id)
        
    except Exception as e:
        print(f'Error handling conversation closed: {e}')

if __name__ == '__main__':
    print("Starting Intercom webhook server...")
    print(f"Bot Admin ID: {config.BOT_ADMIN_ID}")
    print(f"Testing mode: {config.TESTING}")
    print(f"Port: {config.FLASK_PORT}")
    
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.FLASK_DEBUG) 