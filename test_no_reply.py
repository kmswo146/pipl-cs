#!/usr/bin/env python3
"""
Test script to verify no reply behavior when step 1 fails
"""
import sys
import os

# Add worker directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker', 'steps'))

# Mock the dependencies
class MockConfig:
    pass

class MockDB:
    @staticmethod
    def is_bot_active():
        return True

class MockOpenAIUtils:
    @staticmethod
    def call_openai_with_retry(messages, **kwargs):
        # Mock step 0 to always return PROPER_QUESTION (pass to step 1)
        if "categorize" in messages[0]['content'].lower():
            return MockResponse('{"category": "PROPER_QUESTION", "confidence": 0.8}')
        # Mock step 1 to return low confidence (no match)
        else:
            return MockResponse('{"num": 0, "confidence": 0.3}')

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
sys.modules['db'] = MockDB()
sys.modules['openai_utils'] = MockOpenAIUtils()

# Mock FAQ database to return empty
class MockQAEntries:
    @staticmethod
    def find(query):
        return []  # No FAQ entries

MockDB.qa_entries = MockQAEntries()

# Now import the reply engine
from reply_engine import reply_engine

def test_no_reply():
    """Test that no reply is sent when step 1 fails"""
    
    # Mock conversation history
    conversation_history = [
        {
            "role": "user",
            "message": "How do I integrate with Zapier?"
        }
    ]
    
    # Mock conversation document
    conv_doc = {"conversation_id": "test123"}
    
    print("=" * 60)
    print("TESTING NO REPLY BEHAVIOR")
    print("=" * 60)
    print("Message: 'How do I integrate with Zapier?'")
    print("Expected: Step 0 → Step 1 → No Reply (empty string)")
    print("-" * 60)
    
    try:
        result = reply_engine.generate(conversation_history, conv_doc)
        
        print(f"Result: '{result}'")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if result else 'None'}")
        
        if result == "":
            print("✅ SUCCESS: No reply sent (empty string returned)")
        elif result is None:
            print("✅ SUCCESS: No reply sent (None returned)")
        else:
            print(f"❌ FAIL: Unexpected reply sent: '{result}'")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_no_reply() 