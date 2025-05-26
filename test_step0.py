#!/usr/bin/env python3
"""
Simple test script for Step 0 categorization system
"""
import sys
import os

# Add worker/steps to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker', 'steps'))

# Mock the dependencies that step0 needs
class MockConfig:
    pass

class MockOpenAIUtils:
    @staticmethod
    def call_openai_with_retry(messages, **kwargs):
        # Mock OpenAI response based on the message content
        user_message = messages[1]['content'].lower()
        
        if 'bug' in user_message or 'error' in user_message or 'broken' in user_message:
            return MockResponse('{"category": "BUG_REPORT", "confidence": 0.9}')
        elif 'ok' in user_message or 'thanks' in user_message or 'got it' in user_message:
            return MockResponse('{"category": "NO_FOLLOWUP_REPLY", "confidence": 0.95}')
        elif 'hello' in user_message and len(user_message.split()) <= 3:
            return MockResponse('{"category": "GREETING_ONLY", "confidence": 0.85}')
        elif any(word in user_message for word in ['hola', 'bonjour', 'guten tag']):
            return MockResponse('{"category": "NON_ENGLISH", "confidence": 0.9}')
        else:
            return MockResponse('{"category": "PROPER_QUESTION", "confidence": 0.8}')

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

# Mock the modules
sys.modules['config'] = MockConfig()
sys.modules['openai_utils'] = MockOpenAIUtils()

# Now import step0
from step0_categorize import categorize_message

def test_categorization():
    """Test different message types"""
    
    test_cases = [
        {
            "message": "I found a bug in your system",
            "expected_category": "BUG_REPORT",
            "expected_action": "random_reply_then_step2"
        },
        {
            "message": "ok thanks",
            "expected_category": "NO_FOLLOWUP_REPLY", 
            "expected_action": "no_action"
        },
        {
            "message": "hello",
            "expected_category": "GREETING_ONLY",
            "expected_action": "random_reply_only"
        },
        {
            "message": "hola como estas",
            "expected_category": "NON_ENGLISH",
            "expected_action": "random_reply_only"
        },
        {
            "message": "How do I set up email campaigns?",
            "expected_category": "PROPER_QUESTION",
            "expected_action": "pass_to_step1"
        }
    ]
    
    print("=" * 60)
    print("TESTING STEP 0 CATEGORIZATION SYSTEM")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['message']}'")
        print("-" * 40)
        
        try:
            category, action, reply_text, next_step = categorize_message(test['message'])
            
            print(f"✓ Category: {category}")
            print(f"✓ Action: {action}")
            print(f"✓ Reply: {reply_text}")
            print(f"✓ Next Step: {next_step}")
            
            # Check if results match expectations
            if category == test['expected_category'] and action == test['expected_action']:
                print("✅ PASS - Categorization correct!")
            else:
                print(f"❌ FAIL - Expected category: {test['expected_category']}, action: {test['expected_action']}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_categorization() 