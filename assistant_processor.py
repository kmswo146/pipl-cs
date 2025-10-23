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
            if conversation_data:
                history = intercom_api.extract_conversation_history(conversation_data, limit_messages=10)
                context = self._format_conversation_context(history)
            
            # Generate AI response based on the command and context
            response = self._generate_assistant_response(command, context, conversation_id)
            
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
    
    def _generate_assistant_response(self, command, context, conversation_id):
        """Generate AI response for assistant command"""
        
        system_prompt = f"""You are {self.assistant_name.title()}, an AI assistant helping customer support admins. 
        You can analyze conversations, suggest responses, summarize issues, research problems, and provide insights.
        
        Be helpful, concise, and professional. When analyzing conversations, focus on:
        - Understanding the customer's main issue
        - Identifying any unresolved problems
        - Suggesting helpful next steps
        - Providing relevant information or insights
        
        Keep responses under 500 words unless more detail is specifically requested."""
        
        user_prompt = f"""Admin command: {command}

Conversation context (last few messages):
{context}

Conversation ID: {conversation_id}

Please help with this request."""
        
        try:
            response = openai_utils.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=config.DEFAULT_MODEL,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating {self.assistant_name} response: {e}")
            return f"I'm having trouble processing your request right now. Please try again later. (Error: {str(e)})"
    
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