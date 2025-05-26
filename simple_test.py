#!/usr/bin/env python3

import random
import re

def get_random_reply(replies_list):
    """Get a random reply from a list of possible replies"""
    if replies_list:
        return random.choice(replies_list)
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
                "You're welcome!",
                "You're welcome",
                "Welcome!",
                "Welcome",
                "Glad we could help!",
                "Happy to help!"
            ]
            return get_random_reply(gratitude_replies)
    
    # Default: if it's categorized as ISSUE_RESOLVED but doesn't match patterns, no reply
    print(f"DEBUG: Issue resolved but no specific pattern matched: '{clean_msg}' - no reply")
    return None

def test_smart_resolution_replies():
    """Test the smart resolution reply function"""
    
    print("=" * 60)
    print("TESTING ISSUE_RESOLVED SMART REPLIES")
    print("=" * 60)
    
    # Test cases: (message, expected_behavior)
    test_cases = [
        # Gratitude expressions (should get replies)
        ("thanks", "should_reply"),
        ("thank you", "should_reply"),
        ("thank you so much", "should_reply"),
        ("thanks a lot", "should_reply"),
        ("appreciate it", "should_reply"),
        ("that's awesome", "should_reply"),
        ("perfect, thanks", "should_reply"),
        ("excellent work", "should_reply"),
        ("that worked great", "should_reply"),
        ("problem solved, thanks", "should_reply"),
        
        # Simple acknowledgments (no reply)
        ("ok", "no_reply"),
        ("okay", "no_reply"),
        ("got it", "no_reply"),
        ("understood", "no_reply"),
        ("sure", "no_reply"),
        ("alright", "no_reply"),
        ("k", "no_reply"),
        
        # Edge cases
        ("thanks ok", "should_reply"),  # Contains gratitude
        ("ok thanks", "should_reply"),  # Contains gratitude
        ("random message", "no_reply"),  # Doesn't match patterns
        ("", "no_reply"),  # Empty message
    ]
    
    passed = 0
    total = len(test_cases)
    
    for message, expected in test_cases:
        reply = get_smart_resolution_reply(message)
        
        if expected == "should_reply":
            if reply:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
            print(f"{status} '{message}' → {reply}")
        else:  # no_reply
            if reply is None:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
            print(f"{status} '{message}' → {reply}")
    
    print("\n" + "=" * 60)
    print(f"TEST COMPLETE: {passed}/{total} tests passed")
    print("=" * 60)

if __name__ == "__main__":
    test_smart_resolution_replies() 