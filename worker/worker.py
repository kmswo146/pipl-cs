import time
import sys
import os
import random

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
        
        # TIMING VALIDATION: Check if conversation data is fresh enough
        conversation_updated_at = full_history_data.get('updated_at')
        last_user_ts = conv_doc.get('last_user_ts')
        
        if conversation_updated_at and last_user_ts:
            # Convert timestamps for comparison
            from datetime import datetime
            if isinstance(conversation_updated_at, int):
                conv_update_time = datetime.fromtimestamp(conversation_updated_at)
            else:
                # Handle ISO format
                conv_update_time = datetime.fromisoformat(conversation_updated_at.replace('Z', '+00:00'))
            
            # If our database shows a newer user message than what Intercom API returns,
            # the API data is stale - skip this round and let it retry later
            if last_user_ts > conv_update_time:
                print(f"WARNING: Conversation data appears stale!")
                print(f"  DB last_user_ts: {last_user_ts}")
                print(f"  Intercom updated_at: {conv_update_time}")
                print(f"  Skipping this round - will retry later when API data is fresh")
                return
        
        # Extract conversation history (last 20 messages)
        conversation_history = intercom_api.extract_conversation_history(full_history_data, limit_messages=20)
        
        print(f"DEBUG: Conversation history: {len(conversation_history)} messages")
        
        # ADDITIONAL VALIDATION: Check if the latest message timestamp makes sense
        if conversation_history:
            latest_msg = conversation_history[-1]
            latest_msg_ts = latest_msg.get('timestamp')
            if latest_msg_ts and last_user_ts:
                # Convert latest message timestamp
                if isinstance(latest_msg_ts, int):
                    latest_time = datetime.fromtimestamp(latest_msg_ts)
                else:
                    latest_time = datetime.fromisoformat(latest_msg_ts.replace('Z', '+00:00'))
                
                # If the latest message is much older than our trigger time, data is stale
                time_diff = abs((last_user_ts - latest_time).total_seconds())
                if time_diff > 300:  # 5 minutes tolerance
                    print(f"WARNING: Latest message timestamp mismatch!")
                    print(f"  Expected around: {last_user_ts}")
                    print(f"  Latest message: {latest_time}")
                    print(f"  Difference: {time_diff} seconds")
                    print(f"  Skipping - likely stale API data")
                    return
        
        # DEBUG: Print detailed message content to see what Intercom returns
        print("DEBUG: Detailed conversation history:")
        for i, msg in enumerate(conversation_history):
            print(f"  Message {i+1}: role={msg['role']}")
            print(f"    Raw message: {repr(msg['message'])}")
            print(f"    Message length: {len(msg['message'])}")
            print(f"    Timestamp: {msg.get('timestamp')}")
            if msg.get('attachments'):
                print(f"    Attachments: {len(msg['attachments'])} items")
                for j, att in enumerate(msg['attachments']):
                    print(f"      Attachment {j+1}: type={att.get('type')}, content_type={att.get('content_type')}, name={att.get('name')}")
                    print(f"        ALL FIELDS: {att}")  # Print entire attachment object
            print()
        
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
            print(f"No reply generated for conversation {conversation_id} - marking as processed")
            # Mark as processed even when no reply is sent to avoid infinite loop
            db.mark_bot_replied(conversation_id)
            
    except Exception as e:
        print(f"Error handling conversation {conversation_id}: {e}")

def worker_loop():
    """Main worker loop - runs continuously"""
    print(f"Starting bot worker with {config.DELAY_MIN_SECONDS}-{config.DELAY_MAX_SECONDS}s random delay...")
    print(f"Bot Admin ID: {config.BOT_ADMIN_ID}")
    print(f"Testing mode: {config.TESTING}")
    
    while True:
        try:
            # Calculate random delay for this iteration
            delay_seconds = random.randint(config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS)
            #print(f"Using {delay_seconds}s delay for this check...")
            
            # Get conversations that need replies
            pending_conversations = db.get_pending_conversations(delay_seconds)
            
            if pending_conversations:
                print(f"Found {len(pending_conversations)} conversations needing replies")
                
                for conv in pending_conversations:
                    handle_conversation(conv)
                    
                    # Small delay between conversations to avoid rate limiting
                    time.sleep(1)
            else:
                print("No pending conversations found")
            
            # Wait before next scan
            #print(f"Sleeping for 10 seconds...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("Worker stopped by user")
            break
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    worker_loop() 