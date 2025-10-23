from flask import Flask, request, jsonify
import config
import db
from assistant_processor import assistant_processor

app = Flask(__name__)

@app.route('/webhook/', methods=['POST'])
def webhook():
    data = request.json
    topic = data.get('topic', 'unknown')
    
    print(f'Received Intercom webhook - Topic: {topic}')
    # print(f'DEBUG: Full webhook payload: {data}')
    
    try:
        if topic in ['conversation.user.created', 'conversation.user.replied']:
            handle_user_message(data)
        elif topic == 'conversation.admin.replied':
            handle_admin_reply(data)
        elif topic == 'conversation.admin.closed':
            handle_conversation_closed(data)
        elif topic == 'conversation.admin.noted':
            print(f'DEBUG: Processing admin note webhook')
            handle_admin_note(data)
        else:
            print(f'Unhandled topic: {topic}')
            print(f'DEBUG: Available topics we handle: conversation.user.created, conversation.user.replied, conversation.admin.replied, conversation.admin.closed, conversation.admin.noted')
            
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

def handle_admin_note(data):
    """Handle admin note creation events"""
    try:
        conversation_id = data['data']['item']['id']
        
        # Extract note content and admin info
        # Note: The exact structure may vary, we'll handle different possible structures
        note_content = None
        admin_id = None
        
        # Try different possible webhook structures for notes
        item = data['data']['item']
        
        # Method 1: Note might be in conversation_parts
        if 'conversation_parts' in item:
            parts = item['conversation_parts'].get('conversation_parts', [])
            if parts:
                latest_part = parts[0]  # Assuming latest is first
                if latest_part.get('part_type') == 'note':
                    note_content = latest_part.get('body', '')
                    admin_id = latest_part.get('author', {}).get('id')
        
        # Method 2: Note might be directly in item
        if not note_content and 'body' in item:
            note_content = item.get('body', '')
            admin_id = item.get('author', {}).get('id')
        
        # Method 3: Note might be in a 'note' field
        if not note_content and 'note' in item:
            note_content = item['note'].get('body', '')
            admin_id = item['note'].get('author', {}).get('id')
        
        print(f'Admin note in conversation {conversation_id}')
        print(f'Note content: {note_content}')
        print(f'Admin ID: {admin_id}')
        
        if not note_content:
            print('No note content found in webhook payload')
            return
        
        # Check if this note is from the bot itself (prevent infinite loop)
        if str(admin_id) == str(config.BOT_ADMIN_ID):
            print(f'Note from bot itself (admin_id: {admin_id}) - ignoring to prevent loop')
            return
        
        # Check if this is an assistant command
        if assistant_processor.is_assistant_command(note_content):
            print(f'Detected {config.BOT_ASSISTANT_NAME} command in note')
            
            # Process the command
            response = assistant_processor.process_assistant_note(conversation_id, note_content, admin_id)
            
            if response:
                # Send the response back as a note
                success = assistant_processor.send_note_reply(conversation_id, response, config.BOT_ADMIN_ID)
                
                if success:
                    print(f'Successfully processed {config.BOT_ASSISTANT_NAME} command')
                else:
                    print(f'Failed to send {config.BOT_ASSISTANT_NAME} response')
        else:
            print(f'Note does not start with {config.BOT_ASSISTANT_NAME} - ignoring')
            
    except Exception as e:
        print(f'Error handling admin note: {e}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')

if __name__ == '__main__':
    print("Starting Intercom webhook server...")
    print(f"Bot Admin ID: {config.BOT_ADMIN_ID}")
    print(f"Testing mode: {config.TESTING}")
    print(f"Port: {config.FLASK_PORT}")
    
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.FLASK_DEBUG) 