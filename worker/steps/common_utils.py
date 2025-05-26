import random
import re

def get_random_reply(replies_list):
    """Get a random reply from a list of possible replies"""
    if replies_list:
        return random.choice(replies_list)
    return None

def clean_html(text):
    """Clean HTML tags from text content while preserving important elements"""
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

def build_conversation_context(conversation_history, limit_messages=10):
    """Build conversation context string from history"""
    if not conversation_history:
        return ""
    
    context = "\nRecent conversation history:\n"
    for msg in conversation_history[-limit_messages:]:
        if msg['message'].strip():
            clean_msg = clean_html(msg['message'])
            role = "Customer" if msg['role'] == 'user' else "Support"
            context += f"{role}: {clean_msg}\n"
    
    return context 