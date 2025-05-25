import requests
import config

class IntercomAPI:
    def __init__(self):
        self.base_url = "https://api.intercom.io"
        self.headers = {
            'Authorization': f'Bearer {config.INTERCOM_ACCESS_TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_conversation(self, conversation_id):
        """Get full conversation details"""
        url = f'{self.base_url}/conversations/{conversation_id}'
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.ok:
                return response.json()
            else:
                print(f"Failed to get conversation {conversation_id}: {response.text}")
                return None
        except Exception as e:
            print(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    def reply(self, conversation_id, message, admin_id=None):
        """Send a reply to a conversation"""
        if admin_id is None:
            admin_id = config.BOT_ADMIN_ID
            
        url = f'{self.base_url}/conversations/{conversation_id}/reply'
        
        payload = {
            "type": "admin",
            "admin_id": str(admin_id),
            "message_type": "comment",
            "body": message
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.ok:
                print(f"Successfully sent reply to conversation {conversation_id}")
                return True
            else:
                print(f"Failed to send reply to {conversation_id}: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending reply to {conversation_id}: {e}")
            return False
    
    def extract_conversation_history(self, conversation_data, limit_messages=20):
        """Extract conversation history in a clean format, limited to recent messages"""
        if not conversation_data:
            return []
        
        history = []
        
        # Add initial message
        source = conversation_data.get('source', {})
        if source:
            history.append({
                'role': 'user',
                'message': source.get('body', ''),
                'timestamp': source.get('created_at'),
                'author': source.get('author', {})
            })
        
        # Add conversation parts
        parts = conversation_data.get('conversation_parts', {}).get('conversation_parts', [])
        for part in parts:
            if part.get('part_type') == 'comment':
                author = part.get('author', {})
                role = 'admin' if author.get('type') == 'admin' else 'user'
                
                history.append({
                    'role': role,
                    'message': part.get('body', ''),
                    'timestamp': part.get('created_at'),
                    'author': author
                })
        
        # Return only the last N messages (most recent)
        if limit_messages and len(history) > limit_messages:
            history = history[-limit_messages:]
            print(f"DEBUG: Limited conversation history to last {limit_messages} messages")
        
        return history
    
    def extract_unresolved_context(self, conversation_data, limit_messages=20):
        """Extract conversation history focusing on unresolved questions/issues"""
        full_history = self.extract_conversation_history(conversation_data, limit_messages)
        
        if not full_history:
            return []
        
        # Find unresolved questions by looking for user messages not followed by admin responses
        unresolved_context = []
        pending_user_messages = []
        
        for i, msg in enumerate(full_history):
            if msg['role'] == 'user':
                # Add user message to pending
                pending_user_messages.append(msg)
            elif msg['role'] == 'admin':
                # Admin responded - check if it addresses pending user messages
                admin_msg = msg['message'].lower()
                
                # Simple heuristic: if admin message is substantial (>10 chars) and not just acknowledgment
                if len(admin_msg.strip()) > 10 and not self._is_acknowledgment_only(admin_msg):
                    # Consider pending user messages as addressed
                    pending_user_messages = []
                
                # Always include admin messages for context
                unresolved_context.append(msg)
        
        # Add any remaining unresolved user messages
        unresolved_context.extend(pending_user_messages)
        
        # Sort by timestamp to maintain chronological order
        unresolved_context.sort(key=lambda x: x.get('timestamp', 0))
        
        print(f"DEBUG: Found {len(pending_user_messages)} unresolved user messages out of {len(full_history)} total")
        
        return unresolved_context
    
    def _is_acknowledgment_only(self, message):
        """Check if admin message is just an acknowledgment without substantial help"""
        acknowledgments = [
            'ok', 'okay', 'thanks', 'got it', 'received', 'noted', 'sure', 
            'will check', 'looking into', 'let me check', 'one moment'
        ]
        
        message_clean = message.strip().lower()
        return any(ack in message_clean for ack in acknowledgments) and len(message_clean) < 30
    
    def get_last_user_message(self, conversation_data):
        """Get the most recent user message from conversation"""
        history = self.extract_conversation_history(conversation_data)
        
        # Find the last user message
        for msg in reversed(history):
            if msg['role'] == 'user' and msg['message'].strip():
                return msg['message']
        
        return ""

# Global instance
intercom_api = IntercomAPI() 