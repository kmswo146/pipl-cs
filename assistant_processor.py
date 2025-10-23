"""
AI Assistant Note Processor
Handles admin notes that start with the configured assistant name and performs AI-powered actions
"""

import re
import config
import openai_utils
import sys
import os

# Add worker directory to path for intercom_api import
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))
from intercom_api import intercom_api

# Import function library
from assistant_functions import get_functions_documentation, execute_function
from reasoning_engine import reasoning_engine


class AssistantProcessor:
    def __init__(self):
        self.assistant_name = config.BOT_ASSISTANT_NAME
    
    def is_assistant_command(self, note_text):
        """Check if a note starts with the assistant name (case insensitive)"""
        if not note_text:
            return False
        
        # Remove HTML tags and whitespace, then check if starts with assistant name
        clean_text = re.sub(r'<[^>]+>', '', note_text).strip()
        return clean_text.lower().startswith(self.assistant_name.lower())
    
    def process_assistant_note(self, conversation_id, note_text, admin_id):
        """Process an assistant command and return a response"""
        try:
            print(f"Processing {self.assistant_name} command in conversation {conversation_id}")
            print(f"Command text: {note_text}")
            
            # Extract the command (everything after assistant name)
            clean_text = re.sub(r'<[^>]+>', '', note_text).strip()
            command = clean_text[len(self.assistant_name):].strip()  # Remove assistant name and whitespace
            
            if not command:
                return f"Hi! I'm {self.assistant_name.title()}, your AI assistant. What would you like me to help with?"
            
            # Get conversation context for better responses
            conversation_data = intercom_api.get_conversation(conversation_id)
            context = ""
            user_email = None
            
            if conversation_data:
                history = intercom_api.extract_conversation_history(conversation_data, limit_messages=10)
                context = self._format_conversation_context(history)
                
                # Extract user email from conversation
                user_email = self._extract_user_email(conversation_data)
            
            # Generate AI response based on the command and context
            response = self._generate_assistant_response(command, context, conversation_id, user_email)
            
            return response
            
        except Exception as e:
            print(f"Error processing {self.assistant_name} command: {e}")
            return f"Sorry, I encountered an error processing your request: {str(e)}"
    
    def _format_conversation_context(self, history):
        """Format conversation history for AI context"""
        if not history:
            return "No conversation history available."
        
        context_lines = []
        for msg in history[-5:]:  # Last 5 messages for context
            role = msg['role'].upper()
            message = msg['message'][:200] + "..." if len(msg['message']) > 200 else msg['message']
            context_lines.append(f"{role}: {message}")
        
        return "\n".join(context_lines)
    
    def _extract_user_email(self, conversation_data):
        """Extract the user's email from conversation data"""
        try:
            # Get user email from the conversation source
            source = conversation_data.get('source', {})
            author = source.get('author', {})
            user_email = author.get('email', '')
            
            if user_email:
                print(f"DEBUG: Extracted user email from conversation: {user_email}")
                return user_email
            
            # Fallback: try to get from conversation parts (first user message)
            parts = conversation_data.get('conversation_parts', {}).get('conversation_parts', [])
            for part in parts:
                if part.get('author', {}).get('type') == 'user':
                    email = part.get('author', {}).get('email', '')
                    if email:
                        print(f"DEBUG: Extracted user email from conversation parts: {email}")
                        return email
            
            print("DEBUG: No user email found in conversation data")
            return None
            
        except Exception as e:
            print(f"Error extracting user email: {e}")
            return None
    
    def _generate_assistant_response(self, command, context, conversation_id, user_email=None):
        """Generate AI response using shared reasoning engine"""
        
        # Prepare context data for reasoning engine
        context_data = {
            "user_email": user_email,
            "conversation_id": conversation_id,
            "conversation_context": context
        }
        
        # Use shared reasoning engine in self-thinking mode
        result = reasoning_engine.execute_reasoning(
            query=command,
            context_data=context_data,
            mode="self_thinking",
            max_iterations=5
        )
        
        return result.get("answer", "I couldn't complete the reasoning process.")
    
    # OLD METHODS - Now using shared reasoning engine
    # The agentic reasoning logic has been moved to reasoning_engine.py
    
    def _format_function_result(self, func_name, result):
        """Format function results in a user-friendly way"""
        try:
            if func_name == "check_user_plan":
                # NO TRIMMING for user plan - return complete information
                return self._format_user_plan_result(result)
            else:
                # Generic formatting for other functions
                if isinstance(result, dict):
                    # Extract key information if it's a dict
                    key_info = []
                    for key, value in result.items():
                        if key in ['error', 'message', 'status']:
                            key_info.append(f"{key}: {value}")
                        elif isinstance(value, (str, int, float, bool)):
                            key_info.append(f"{key}: {value}")
                    
                    if key_info:
                        return " | ".join(key_info[:3])  # Limit to first 3 key items
                
                return str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                
        except Exception as e:
            print(f"Error formatting function result: {e}")
            # Even for errors, don't trim user plan results
            if func_name == "check_user_plan":
                return str(result)
            return str(result)[:100] + "..."
    
    def _format_user_plan_result(self, result):
        """Format check_user_plan results - show ALL workspace information"""
        try:
            if isinstance(result, dict):
                # Don't trim - return the full result so AI can see all workspaces
                # Just clean up HTML in email fields
                clean_result = self._clean_html_from_result(result)
                
                # Return more complete information
                return str(clean_result)
            
            return str(result)
            
        except Exception as e:
            print(f"Error formatting user plan result: {e}")
            return str(result)
    
    def _clean_html_from_result(self, result):
        """Clean HTML tags from result data"""
        import re
        
        def clean_value(value):
            if isinstance(value, str) and '<a href="mailto:' in value:
                # Extract email from HTML
                email_match = re.search(r'mailto:([^"]+)', value)
                if email_match:
                    return email_match.group(1)
            elif isinstance(value, str) and '<a href="' in value:
                # Extract URL from HTML
                url_match = re.search(r'href="([^"]+)"', value)
                if url_match:
                    return url_match.group(1)
            elif isinstance(value, str):
                # Remove any other HTML tags
                return re.sub(r'<[^>]+>', '', value)
            
            return value
        
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            else:
                return clean_value(d)
        
        return clean_dict(result)
    
    def send_note_reply(self, conversation_id, response_text, admin_id):
        """Send assistant's response as an admin note"""
        try:
            # Format the response with assistant branding
            formatted_response = f"🤖 **{self.assistant_name.title()}'s Response:**\n\n{response_text}"
            
            # Send as admin note using the new send_note method
            success = intercom_api.send_note(conversation_id, formatted_response, admin_id)
            
            if success:
                print(f"{self.assistant_name} response sent successfully to conversation {conversation_id}")
                return True
            else:
                print(f"Failed to send {self.assistant_name} response to conversation {conversation_id}")
                return False
                
        except Exception as e:
            print(f"Error sending {self.assistant_name} response: {e}")
            return False


# Global instance
assistant_processor = AssistantProcessor()