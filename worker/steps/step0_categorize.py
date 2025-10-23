import sys
import os
import random
import re

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from openai_utils import call_openai_with_retry
from common_utils import get_random_reply, clean_html, build_conversation_context

# Sticky prompt for message categorization
STICKY_PROMPT = """You are a message categorizer for PlusVibe.ai (formely call pipl.ai) customer support. Analyze the ENTIRE conversation context and categorize the customer's intent into one of these types:

1. BUG_REPORT - Customer is reporting a bug, issue, or problem with the service
2. NO_FOLLOWUP_REPLY - Simple acknowledgments like "ok", "thanks", "got it" that don't expect a response
3. PROPER_QUESTION - A genuine question or request that needs a detailed answer
4. NON_ENGLISH - Message is not in English
5. GREETING_ONLY - Just a greeting without any specific question or context
6. UNHAPPY_WITH_ADMIN - Customer is expressing dissatisfaction with a previous admin response OR asking the same/similar question again after receiving an admin response (indicating they weren't satisfied with the previous answer)
7. PROMOTIONAL_EMAIL - Marketing or promotional content, advertisements, spam, or unsolicited commercial messages. Only categorize as this if you are highly confident (>0.9) it's promotional content.
8. ISSUE_RESOLVED - Customer is indicating their issue has been resolved or expressing satisfaction/gratitude after receiving help. Look at the conversation context to determine if this is a resolution response.

Return JSON format:
{"category": "[CATEGORY_NAME]", "confidence": [0.0 to 1.0]}

CRITICAL INSTRUCTIONS:
1. ANALYZE THE ENTIRE CONVERSATION CONTEXT, not just the last message
2. When the current message is vague or general (like "I expect an answer", "please help", "any update?", "hi"), look at the FULL conversation history to understand what the customer is actually asking about
3. If they have asked specific questions earlier in the conversation, treat the current message as a PROPER_QUESTION that should trigger answering those previous questions
4. Consider the conversation flow: if a customer asked a detailed question earlier and now sends a brief follow-up, it's still about their original question
5. For images/attachments, consider them as part of the customer's question or issue

IMPORTANT: For ISSUE_RESOLVED category, consider the conversation context - this should be used when the customer is responding positively after receiving help or indicating their problem is solved.
IMPORTANT: For UNHAPPY_WITH_ADMIN category, look for:
- Direct expressions of dissatisfaction ("this doesn't work", "that's not helpful", "I already tried that")
- Escalation language ("I need to speak to someone else", "this isn't working")
- Repeated questions after receiving admin responses (indicates dissatisfaction with previous answers)
"""

# Category configurations - easy to modify and extend
CATEGORY_ACTIONS = {
    "BUG_REPORT": {
        "action": "random_reply_then_step2",
        "replies": [
            "Let us check",
            "let us check",
            "checking",
            "let us look into this"
        ]
    },
    "NO_FOLLOWUP_REPLY": {
        "action": "no_action",
        "replies": []
    },
    "PROPER_QUESTION": {
        "action": "pass_to_step1",
        "replies": []
    },
    "NON_ENGLISH": {
        "action": "random_reply_only",
        "replies": [
            "How can we help?",
            "Hi, how can we help?",
            "hi"
        ]
    },
    "GREETING_ONLY": {
        "action": "random_reply_only",
        "replies": [
            "How can we help?",
            "Hi, how can we help?",
            "hi"
        ]
    },
    "UNHAPPY_WITH_ADMIN": {
        "action": "no_action",
        "replies": []
    },
    "PROMOTIONAL_EMAIL": {
        "action": "no_action",
        "replies": []
    },
    "ISSUE_RESOLVED": {
        "action": "smart_resolution_reply",
        "replies": []
    }
}

def get_category_random_reply(category):
    """Get a random reply for the given category"""
    if category in CATEGORY_ACTIONS and CATEGORY_ACTIONS[category]["replies"]:
        return get_random_reply(CATEGORY_ACTIONS[category]["replies"])
    return None

def get_smart_resolution_reply(user_message):
    """Analyze the user's resolution message and return appropriate reply"""
    # Clean and normalize the message
    clean_msg = re.sub(r'<[^>]+>', '', user_message).lower().strip()
    
    # Patterns that indicate gratitude/thanks
    gratitude_patterns = [
        r'\bthank\b', r'\bthanks\b', r'\bthx\b', r'\bty\b',
        r'\bappreciate\b', r'\bawesome\b', r'\bgreat\b',
        r'\bperfect\b', r'\bexcellent\b', r'\bwonderful\b',
        r'\bfantastic\b', r'\bamazing\b', r'\bhelpful\b',
        r'\bthank you\b', r'\bthat works\b', r'\bthat worked\b',
        r'\bsolved\b', r'\bfixed\b', r'\bresolved\b'
    ]
    
    # Patterns that are just simple acknowledgments
    simple_ack_patterns = [
        r'^\s*ok\s*$', r'^\s*okay\s*$', r'^\s*k\s*$',
        r'^\s*got it\s*$', r'^\s*understood\s*$',
        r'^\s*alright\s*$', r'^\s*sure\s*$'
    ]
    
    # Check for simple acknowledgments first (no reply needed)
    for pattern in simple_ack_patterns:
        if re.search(pattern, clean_msg):
            print(f"DEBUG: Detected simple acknowledgment: '{clean_msg}' - no reply needed")
            return None
    
    # Check for gratitude expressions (send thank you reply)
    for pattern in gratitude_patterns:
        if re.search(pattern, clean_msg):
            print(f"DEBUG: Detected gratitude expression: '{clean_msg}' - sending thank you reply")
            gratitude_replies = [
                "You're welcome",
                "you're welcome",
                "Welcome!",
                "Welcome",
                "sure, anytime",
                "Glad we could help",
                "Happy to help"
            ]
            return get_random_reply(gratitude_replies)
    
    # Default: if it's categorized as ISSUE_RESOLVED but doesn't match patterns, no reply
    print(f"DEBUG: Issue resolved but no specific pattern matched: '{clean_msg}' - no reply")
    return None

def categorize_message(user_message, conversation_history=None):
    """
    Categorize the user message and return the appropriate action
    Returns: (category, action, reply_text, next_step)
    """
    try:
        print(f"DEBUG: Step 0 - Categorizing message: {user_message}")
        
        # Build conversation context if provided
        conversation_context = ""
        if conversation_history:
            print(f"DEBUG: Including {len(conversation_history)} messages of conversation context")
            conversation_context = build_conversation_context(conversation_history, 15)  # Increased limit
        
        # Create prompt for AI categorization with context-first approach
        if conversation_context:
            user_content = f"""{conversation_context}

CURRENT MESSAGE: "{user_message}"

Based on the ENTIRE conversation above, categorize the customer's intent. Pay special attention to any previous questions or issues that may not be resolved, and consider how the current message relates to the overall conversation flow."""
        else:
            user_content = f"""Customer message: "{user_message}"

Categorize this message and return JSON with category and confidence."""
        
        messages = [
            {"role": "system", "content": STICKY_PROMPT},
            {"role": "user", "content": user_content}
        ]
        
        print(f"DEBUG: Sending to OpenAI for categorization...")
        print("=" * 80)
        print("CATEGORIZATION PROMPT:")
        print("=" * 80)
        for i, msg in enumerate(messages):
            print(f"Message {i+1} [{msg['role']}]:")
            print(msg['content'])
            print("-" * 40)
        print("=" * 80)
        
        response = call_openai_with_retry(
            messages=messages,
            max_completion_tokens=150,  # Increased for more detailed analysis
            temperature=0.1,  # Low temperature for consistent categorization
            response_format={"type": "json_object"},
            max_retries=3
        )
        
        if response is None:
            print("ERROR: OpenAI API call failed after all retries")
            # Default to PROPER_QUESTION if categorization fails
            return "PROPER_QUESTION", "pass_to_step1", None, 1
        
        ai_response = response.choices[0].message.content.strip()
        print(f"DEBUG: AI categorization response: {ai_response}")
        
        # Parse JSON response
        category, confidence = _parse_categorization_response(ai_response)
        
        print(f"DEBUG: Parsed category: {category}")
        print(f"DEBUG: Parsed confidence: {confidence}")
        
        # Apply confidence thresholds
        if category == "PROMOTIONAL_EMAIL" and confidence < 0.9:
            print(f"DEBUG: PROMOTIONAL_EMAIL confidence ({confidence}) below 0.9 threshold - defaulting to PROPER_QUESTION")
            category = "PROPER_QUESTION"
        elif confidence < 0.7:
            print(f"DEBUG: Low confidence ({confidence}) - defaulting to PROPER_QUESTION")
            category = "PROPER_QUESTION"
        
        # Get action configuration for this category
        if category not in CATEGORY_ACTIONS:
            print(f"DEBUG: Unknown category {category} - defaulting to PROPER_QUESTION")
            category = "PROPER_QUESTION"
        
        action_config = CATEGORY_ACTIONS[category]
        action = action_config["action"]
        
        # Determine reply and next step based on action
        reply_text = None
        next_step = None
        
        if action == "random_reply_then_step2":
            reply_text = get_category_random_reply(category)
            next_step = 2
        elif action == "random_reply_only":
            reply_text = get_category_random_reply(category)
            next_step = None  # No further processing
        elif action == "pass_to_step1":
            reply_text = None
            next_step = 1
        elif action == "no_action":
            reply_text = None
            next_step = None  # No further processing
        elif action == "smart_resolution_reply":
            reply_text = get_smart_resolution_reply(user_message)
            next_step = None  # No further processing
        
        print(f"DEBUG: Category: {category}, Action: {action}, Reply: {reply_text}, Next Step: {next_step}")
        
        return category, action, reply_text, next_step
        
    except Exception as e:
        print(f"ERROR in message categorization: {e}")
        # Default to PROPER_QUESTION if anything goes wrong
        return "PROPER_QUESTION", "pass_to_step1", None, 1

def _parse_categorization_response(ai_response):
    """Parse JSON response to extract category and confidence"""
    try:
        import json
        data = json.loads(ai_response)
        
        category = data.get('category', 'PROPER_QUESTION').upper()
        confidence = float(data.get('confidence', 0.0))
        
        # Ensure confidence is within valid range
        if confidence < 0.0:
            confidence = 0.0
        elif confidence > 1.0:
            confidence = 1.0
            
        return category, confidence
    except Exception as e:
        print(f"ERROR parsing categorization JSON response: {e}")
        print(f"Raw AI response: {ai_response}")
        return "PROPER_QUESTION", 0.0

 