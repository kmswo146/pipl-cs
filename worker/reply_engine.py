import openai
from bson import ObjectId
import config
import db

# Set up Azure OpenAI client
openai_client = openai.AzureOpenAI(
    api_key=config.AZURE_OPENAI_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT
)

class ReplyEngine:
    def __init__(self):
        self.small_faq_id = "6832d2d44284c30bb33e46a5"  # Your password reset Q&A
    
    def generate(self, conversation_history, conv_doc):
        """Main entry point - generate reply based on conversation history"""
        try:
            # Get the last user message
            last_user_msg = self._get_last_user_message(conversation_history)
            if not last_user_msg:
                return "I didn't receive your message clearly. Could you please try again?"
            
            print(f"Processing user message: {last_user_msg}")
            
            # Classify intent
            intent = self._classify_intent(last_user_msg)
            print(f"Classified intent: {intent}")
            
            # Generate response based on intent
            if intent == "password_reset":
                return self._get_faq_answer()
            elif intent == "account_check":
                return self._handle_account_check(conv_doc)
            elif intent == "general_support":
                return self._generate_llm_response(conversation_history)
            else:
                return "Could you clarify that for me? I want to make sure I give you the most helpful response."
                
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "I'm having trouble processing your request right now. Please try again in a moment."
    
    def _get_last_user_message(self, history):
        """Extract the last user message from conversation history"""
        for msg in reversed(history):
            if msg['role'] == 'user' and msg['message'].strip():
                return msg['message'].strip()
        return ""
    
    def _classify_intent(self, user_message):
        """Classify user intent using simple keyword matching (can be enhanced with LLM)"""
        message_lower = user_message.lower()
        
        # Password reset keywords
        password_keywords = ['password', 'reset', 'forgot', 'login', 'sign in', 'access']
        if any(keyword in message_lower for keyword in password_keywords):
            return "password_reset"
        
        # Account check keywords  
        account_keywords = ['account', 'billing', 'subscription', 'plan', 'payment']
        if any(keyword in message_lower for keyword in account_keywords):
            return "account_check"
        
        # Default to general support
        return "general_support"
    
    def _get_faq_answer(self):
        """Get canned answer from MongoDB FAQ"""
        try:
            doc = db.qa_entries.find_one({"_id": ObjectId(self.small_faq_id)})
            if doc:
                return doc.get("answer", "I found information about password reset, but the details aren't available right now.")
            else:
                return "I can help you reset your password. Please check your email for reset instructions, or contact our support team."
        except Exception as e:
            print(f"Error fetching FAQ answer: {e}")
            return "I can help you reset your password. Please contact our support team for assistance."
    
    def _handle_account_check(self, conv_doc):
        """Handle account-related queries (placeholder for future DB integration)"""
        # This is where you'd query your accounts database
        # For now, return a helpful message
        return "I'd be happy to help you with your account. For account-specific information, please provide your account email or contact our support team who can access your account details securely."
    
    def _generate_llm_response(self, conversation_history):
        """Generate response using LLM for general support"""
        try:
            print(f"DEBUG: Starting LLM response generation")
            print(f"DEBUG: Conversation history length: {len(conversation_history)}")
            
            # Build conversation context for LLM
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful customer support assistant. Provide concise, helpful responses. If you're unsure about specific account details or technical issues, direct users to contact the support team."
                }
            ]
            
            # Add recent conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                if msg['message'].strip():
                    role = "user" if msg['role'] == 'user' else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg['message']
                    })
            
            print(f"DEBUG: Built messages for OpenAI: {messages}")
            print(f"DEBUG: Using model/deployment: {config.DEFAULT_MODEL}")
            print(f"DEBUG: OpenAI endpoint: {config.AZURE_OPENAI_ENDPOINT}")
            
            print("DEBUG: Calling OpenAI API...")
            response = openai_client.chat.completions.create(
                model=config.DEFAULT_MODEL,  # deployment name: gpt-4.1
                messages=messages,
                max_completion_tokens=300,
                temperature=0.7
            )
            
            print(f"DEBUG: OpenAI response received: {response}")
            result = response.choices[0].message.content.strip()
            print(f"DEBUG: Extracted content: {result}")
            
            return result
            
        except Exception as e:
            print(f"ERROR generating LLM response: {e}")
            print(f"ERROR type: {type(e)}")
            import traceback
            print(f"ERROR traceback: {traceback.format_exc()}")
            return "I'm here to help! Could you please provide more details about what you need assistance with?"

# Global instance
reply_engine = ReplyEngine() 