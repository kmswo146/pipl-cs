import sys
import os

# Add steps directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'steps'))

from step1_strict_faq import strict_faq_match
import db

class ReplyEngine:
    def __init__(self):
        pass
    
    def generate(self, conversation_history, conv_doc):
        """Main entry point - waterfall logic to handle tickets"""
        try:
            # SAFETY CHECK: Verify bot is active before processing
            print("=" * 50)
            print("SAFETY CHECK: Bot Status")
            print("=" * 50)
            
            if not db.is_bot_active():
                print("SAFETY: Bot is INACTIVE - skipping auto-reply")
                return None  # Return None to indicate no reply should be sent
            
            print("SAFETY: Bot is ACTIVE - proceeding with reply generation")
            
            # Get the last user message
            last_user_msg = self._get_last_user_message(conversation_history)
            if not last_user_msg:
                return "I didn't receive your message clearly. Could you please try again?"
            
            print(f"Processing user message: {last_user_msg}")
            
            # STEP 1: Try strict FAQ matching
            print("=" * 50)
            print("STEP 1: Strict FAQ Matching")
            print("=" * 50)
            
            confidence, faq_answer = strict_faq_match(last_user_msg, conversation_history)
            if confidence >= 0.95 and faq_answer:
                print(f"SUCCESS: Step 1 matched with confidence {confidence}")
                return faq_answer
            
            print(f"Step 1 failed (confidence: {confidence}) - proceeding to fallback")
            
            # STEP 2-4: TODO - implement later
            # For now, fallback
            print("=" * 50)
            print("FALLBACK: No high-confidence match found")
            print("=" * 50)
            
            return "hi"
                
        except Exception as e:
            print(f"Error in reply engine: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return "I'm having trouble processing your request right now. Please try again in a moment."
    
    def _get_last_user_message(self, history):
        """Extract the last user message from conversation history"""
        for msg in reversed(history):
            if msg['role'] == 'user' and msg['message'].strip():
                # Clean HTML from message
                import re
                clean_msg = re.sub(r'<[^>]+>', '', msg['message'])
                return ' '.join(clean_msg.split()).strip()
        return ""

# Global instance
reply_engine = ReplyEngine() 