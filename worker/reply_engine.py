import sys
import os

# Add steps directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'steps'))

from step0_categorize import categorize_message
from step1_strict_faq import strict_faq_match
import db
import config

class ReplyEngine:
    def __init__(self):
        pass
    
    def _should_respect_testing_flag(self, step_number, conv_doc):
        """Check if we should respect the testing flag for this step"""
        # Steps 0 and 1 ignore testing flag (always run)
        if step_number <= 1:
            return False
        
        # Step 2+ respects testing flag
        if config.TESTING:
            user_email = conv_doc.get('user_email', '')
            if user_email != config.TEST_EMAIL:
                print(f"TESTING MODE: Step {step_number} blocked for email {user_email} (not {config.TEST_EMAIL})")
                return True
        
        return False
    
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
                print("DEBUG: No clear user message found - not responding")
                return ""  # Return empty string to indicate no reply needed
            
            print(f"Processing user message: {last_user_msg}")
            
            # STEP 0: Categorize the message (ALWAYS RUNS - ignores testing flag)
            print("=" * 50)
            print("STEP 0: Message Categorization (LIVE - ignores testing flag)")
            print("=" * 50)
            
            category, action, reply_text, next_step = categorize_message(last_user_msg, conversation_history)
            
            # If step 0 provides a direct reply, return it
            if reply_text and next_step is None:
                print(f"SUCCESS: Step 0 handled message with category '{category}' - returning direct reply")
                return reply_text
            
            # If step 0 says no action needed, return None (no reply)
            if action == "no_action":
                print(f"SUCCESS: Step 0 determined no action needed for category '{category}'")
                return ""  # Return empty string to indicate no reply needed
            
            # If step 0 provides a reply but wants to continue to next step
            if reply_text and next_step == 2:
                print(f"Step 0 provided reply for category '{category}' and wants to continue to step 2")
                
                # Check testing flag for step 2
                if self._should_respect_testing_flag(2, conv_doc):
                    print("TESTING MODE: Step 2 blocked - returning step 0 reply only")
                    return reply_text
                
                print(f"SUCCESS: Step 0 provided reply for category '{category}' and will continue to step 2")
                # TODO: Implement step 2 for bug reports
                return reply_text
            
            # If step 0 wants to pass to step 1
            if next_step == 1:
                print(f"Step 0 categorized as '{category}' - proceeding to Step 1")
                
                # STEP 1: Try strict FAQ matching (ALWAYS RUNS - ignores testing flag)
                print("=" * 50)
                print("STEP 1: Strict FAQ Matching (LIVE - ignores testing flag)")
                print("=" * 50)
                
                confidence, faq_answer = strict_faq_match(last_user_msg, conversation_history)
                if confidence >= 0.95 and faq_answer:
                    print(f"SUCCESS: Step 1 matched with confidence {confidence}")
                    return faq_answer
                
                print(f"Step 1 failed (confidence: {confidence}) - would proceed to step 2+")
                
                # Check testing flag for step 2+
                if self._should_respect_testing_flag(2, conv_doc):
                    print("TESTING MODE: Step 2+ blocked - no reply will be sent")
                    return ""
                
                print("Step 2+ would run here (not yet implemented)")
            
            # STEP 2-4: TODO - implement later
            # For now, no fallback - just don't reply
            print("=" * 50)
            print("NO REPLY: No high-confidence match found")
            print("=" * 50)
            
            return ""  # Return empty string to indicate no reply needed
                
        except Exception as e:
            print(f"Error in reply engine: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return "I'm having trouble processing your request right now. Please try again in a moment."
    
    def _get_last_user_message(self, history):
        """Extract the last user message from conversation history"""
        for msg in reversed(history):
            if msg['role'] == 'user':
                # First check if message has attachments
                has_attachments = msg.get('attachments') and len(msg.get('attachments', [])) > 0
                
                # Clean HTML from message
                import re
                clean_msg = re.sub(r'<[^>]+>', '', msg['message']).strip()
                
                print(f"DEBUG: Last user message analysis:")
                print(f"  Raw message: {repr(msg['message'])}")
                print(f"  Clean message: {repr(clean_msg)}")
                print(f"  Has attachments: {has_attachments}")
                if has_attachments:
                    print(f"  Attachment count: {len(msg.get('attachments', []))}")
                    for i, att in enumerate(msg.get('attachments', [])):
                        print(f"    Attachment {i+1}: type={att.get('type')}, content_type={att.get('content_type')}")
                
                # If message has text content, return it
                if clean_msg:
                    return clean_msg
                
                # If message has only attachments (no text), check if they are images
                if has_attachments:
                    for att in msg.get('attachments', []):
                        content_type = att.get('content_type', '')
                        if content_type.startswith('image/'):
                            print(f"DEBUG: Found image-only message - returning empty string (no reply)")
                            return ""  # Return empty string so main logic treats as "no message"
                    
                    # Non-image attachments, treat as regular message
                    print(f"DEBUG: Found non-image attachment - returning attachment description")
                    return msg['message']  # Return the formatted attachment text
                
                print(f"DEBUG: Message has no content and no attachments - skipping")
        
        print(f"DEBUG: No valid user message found in history")
        return ""

# Global instance
reply_engine = ReplyEngine() 