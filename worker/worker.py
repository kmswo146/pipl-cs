import time
import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import db
from intercom_api import intercom_api
from reply_engine import reply_engine

def handle_conversation(conv_doc):
    """Process a single conversation that needs a bot reply"""
    conversation_id = conv_doc["conversation_id"]
    
    try:
        print(f"Processing conversation {conversation_id}")
        
        # Get full conversation history from Intercom
        full_history_data = intercom_api.get_conversation(conversation_id)
        if not full_history_data:
            print(f"Failed to get conversation data for {conversation_id}")
            return
        
        # Extract conversation history (last 20 messages)
        conversation_history = intercom_api.extract_conversation_history(full_history_data, limit_messages=20)
        
        print(f"DEBUG: Conversation history: {len(conversation_history)} messages")
        
        # Generate reply using the reply engine
        reply_text = reply_engine.generate(conversation_history, conv_doc)
        
        if reply_text is None:
            print(f"Bot is INACTIVE - skipping reply for conversation {conversation_id}")
            return
        elif reply_text:
            print(f"Generated reply for {conversation_id}: {reply_text[:100]}...")
            
            # Send reply via Intercom API
            success = intercom_api.reply(conversation_id, reply_text, config.BOT_ADMIN_ID)
            
            if success:
                # Mark as replied in database
                db.mark_bot_replied(conversation_id)
                print(f"Successfully processed conversation {conversation_id}")
            else:
                print(f"Failed to send reply for conversation {conversation_id}")
        else:
            print(f"No reply generated for conversation {conversation_id}")
            
    except Exception as e:
        print(f"Error handling conversation {conversation_id}: {e}")

def worker_loop():
    """Main worker loop - runs continuously"""
    print(f"Starting bot worker with {config.DELAY_SECONDS}s delay...")
    print(f"Bot Admin ID: {config.BOT_ADMIN_ID}")
    print(f"Testing mode: {config.TESTING}")
    
    while True:
        try:
            # Get conversations that need replies
            pending_conversations = db.get_pending_conversations(config.DELAY_SECONDS)
            
            if pending_conversations:
                print(f"Found {len(pending_conversations)} conversations needing replies")
                
                for conv in pending_conversations:
                    handle_conversation(conv)
                    
                    # Small delay between conversations to avoid rate limiting
                    time.sleep(1)
            else:
                print("No pending conversations found")
            
            # Wait before next scan
            print(f"Sleeping for 10 seconds...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("Worker stopped by user")
            break
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    worker_loop() 