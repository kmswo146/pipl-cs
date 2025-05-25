from pymongo import MongoClient
from datetime import datetime, timezone
import config

# MongoDB client setup
mongo_client = MongoClient(config.DASHBOARD_DB_URI)
db = mongo_client.get_default_database()

# Collections
intercom_conversations = db.intercom_conversations
qa_entries = db.qa_entries
settings = db.settings

def utc_now():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

def upsert_conversation(conversation_id, user_id, user_email=None, pending_reply=True, bot_paused=False):
    """Upsert conversation document"""
    update_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "last_user_ts": utc_now(),
        "pending_reply": pending_reply,
        "bot_paused": bot_paused,
        "awaiting_clarification": False
    }
    
    # Always update email if provided (even if empty, for debugging)
    if user_email is not None:
        update_data["user_email"] = user_email
    
    print(f"DEBUG: Upserting conversation with data: {update_data}")
    
    result = intercom_conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": update_data},
        upsert=True
    )
    
    print(f"DEBUG: Upsert result - matched: {result.matched_count}, modified: {result.modified_count}, upserted_id: {result.upserted_id}")
    
    return result

def pause_bot_for_conversation(conversation_id):
    """Pause bot and clear pending reply when human admin takes over"""
    return intercom_conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "pending_reply": False,
                "bot_paused": True
            }
        }
    )

def reset_conversation_flags(conversation_id):
    """Reset flags when conversation is closed"""
    return intercom_conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "pending_reply": False,
                "bot_paused": False,
                "awaiting_clarification": False
            }
        }
    )

def mark_bot_replied(conversation_id):
    """Mark that bot has replied"""
    return intercom_conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "pending_reply": False,
                "awaiting_clarification": False,
                "last_bot_ts": utc_now()
            }
        }
    )

def get_pending_conversations(delay_seconds):
    """Get conversations that need bot replies"""
    from datetime import timedelta
    cutoff = utc_now() - timedelta(seconds=delay_seconds)
    
    filter_query = {
        "pending_reply": True,
        "bot_paused": False,
        "last_user_ts": {"$lte": cutoff}
    }
    
    return list(intercom_conversations.find(filter_query))

def is_bot_active():
    """Check if the Intercom bot is active"""
    try:
        bot_setting = settings.find_one({"key": "intercom_bot"})
        if bot_setting:
            status = bot_setting.get("status", "INACTIVE")
            print(f"DEBUG: Bot status: {status}")
            return status == "ACTIVE"
        else:
            print("DEBUG: No bot status setting found - defaulting to INACTIVE")
            return False
    except Exception as e:
        print(f"ERROR checking bot status: {e}")
        return False  # Fail safe - don't send replies if we can't check status

def set_bot_status(status):
    """Set the Intercom bot status (ACTIVE/INACTIVE)"""
    try:
        result = settings.update_one(
            {"key": "intercom_bot"},
            {"$set": {"key": "intercom_bot", "status": status, "updated_at": utc_now()}},
            upsert=True
        )
        print(f"DEBUG: Bot status set to {status}")
        return result
    except Exception as e:
        print(f"ERROR setting bot status: {e}")
        return None 