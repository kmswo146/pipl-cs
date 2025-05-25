import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
import db
from bson import ObjectId
from openai_utils import call_openai_with_retry

# Sticky prompt for this step
STICKY_PROMPT = """You are a human customer support that follows strict rule (never disclose that you're an AI) for PlusVibe.ai (a cold email automation SaaS). Determine if the customer question EXACTLY matches one of the predefined FAQ questions.

Be EXTREMELY strict - only return a match if you are 100% confident the customer is asking the exact same thing.

Return JSON format:
{"num": [FAQ number if confident, otherwise 0], "confidence": [0.0 to 1.0]}"""

def strict_faq_match(user_message, conversation_history=None):
    """
    Try to match user message against FAQ database with high confidence
    Returns: (confidence_score, faq_answer) or (0.0, None)
    """
    try:
        print(f"DEBUG: Step 1 - Strict FAQ matching for: {user_message}")
        
        # Get all FAQ entries from database
        faq_entries = list(db.qa_entries.find({}))
        
        if not faq_entries:
            print("DEBUG: No FAQ entries found in database")
            return 0.0, None
        
        print(f"DEBUG: Found {len(faq_entries)} FAQ entries")
        
        # Build FAQ context for AI (numbered list)
        faq_context = "Available FAQ questions:\n"
        for i, faq in enumerate(faq_entries):
            faq_context += f"{i+1}. {faq['question']}\n"
        
        # Build conversation context if provided
        conversation_context = ""
        if conversation_history:
            print(f"DEBUG: Including {len(conversation_history)} messages of conversation context")
            conversation_context = "\nConversation history: (oldest on top)\n"
            for msg in conversation_history[-20:]:  # Last 20 messages
                if msg['message'].strip():
                    clean_msg = _clean_html(msg['message'])
                    role = "Customer" if msg['role'] == 'user' else "Support"
                    conversation_context += f"{role}: {clean_msg}\n"
        
        # Create prompt for AI to match
        messages = [
            {"role": "system", "content": STICKY_PROMPT},
            {"role": "user", "content": f"""Customer question: "{user_message}"
{conversation_context}
{faq_context}

Return JSON with FAQ number and confidence."""}
        ]
        
        print(f"DEBUG: Sending to OpenAI for FAQ matching...")
        print("=" * 80)
        print("FULL PROMPT SENT TO OPENAI:")
        print("=" * 80)
        for i, msg in enumerate(messages):
            print(f"Message {i+1} [{msg['role']}]:")
            print(msg['content'])
            print("-" * 40)
        print("=" * 80)
        
        response = call_openai_with_retry(
            messages=messages,
            max_completion_tokens=150,
            temperature=0.1,  # Low temperature for consistent matching
            response_format={"type": "json_object"},
            max_retries=3
        )
        
        if response is None:
            print("ERROR: OpenAI API call failed after all retries")
            return 0.0, None
        
        ai_response = response.choices[0].message.content.strip()
        print(f"DEBUG: AI FAQ matching response: {ai_response}")
        
        # Parse JSON response
        confidence, faq_number = _parse_json_response(ai_response)
        
        print(f"DEBUG: Parsed confidence: {confidence} (type: {type(confidence)})")
        print(f"DEBUG: Parsed FAQ number: {faq_number}")
        
        if confidence >= 0.95 and faq_number > 0:
            # Get the FAQ answer by number (1-indexed)
            if faq_number <= len(faq_entries):
                faq_doc = faq_entries[faq_number - 1]  # Convert to 0-indexed
                # Return the raw answer as-is (don't clean HTML for FAQ answers)
                raw_answer = faq_doc['answer']
                print(f"DEBUG: High confidence match found ({confidence}) - returning predefined answer")
                return confidence, raw_answer
        
        print(f"DEBUG: No high confidence match (confidence: {confidence})")
        return confidence, None
        
    except Exception as e:
        print(f"ERROR in strict FAQ matching: {e}")
        return 0.0, None

def _parse_json_response(ai_response):
    """Parse JSON response to extract confidence and FAQ number"""
    try:
        import json
        data = json.loads(ai_response)
        
        confidence = float(data.get('confidence', 0.0))
        faq_number = int(data.get('num', 0))
        
        # Ensure confidence is within valid range
        if confidence < 0.0:
            confidence = 0.0
        elif confidence > 1.0:
            confidence = 1.0
            
        return confidence, faq_number
    except Exception as e:
        print(f"ERROR parsing JSON response: {e}")
        print(f"Raw AI response: {ai_response}")
        return 0.0, 0

def _clean_html(text):
    """Clean HTML tags from text content while preserving important elements"""
    import re
    if not text:
        return ""
    
    # Replace <br> tags with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Replace <img> tags with [Image: description] or [Image]
    def replace_img(match):
        img_tag = match.group(0)
        # Try to extract alt text or src for description
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
        src_match = re.search(r'src=["\']([^"\']*)["\']', img_tag)
        
        if alt_match:
            return f"[Image: {alt_match.group(1)}]"
        elif src_match:
            # Extract filename from URL
            src = src_match.group(1)
            filename = src.split('/')[-1].split('?')[0]
            return f"[Image: {filename}]"
        else:
            return "[Image]"
    
    text = re.sub(r'<img[^>]*>', replace_img, text, flags=re.IGNORECASE)
    
    # Replace common HTML entities
    text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    text = text.replace('​﻿', '')  # Remove zero-width characters
    
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up extra whitespace but preserve line breaks
    lines = text.split('\n')
    cleaned_lines = [' '.join(line.split()) for line in lines]
    clean_text = '\n'.join(line for line in cleaned_lines if line.strip())
    
    return clean_text.strip() 