#!/usr/bin/env python3
"""
Test script for chain of thought reasoning with OpenAI
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from openai_utils import call_openai_with_retry

def test_reasoning_chain():
    """Test the chain of thought reasoning with OpenAI"""
    
    # The system prompt with reasoning steps
    system_prompt = """You are a support agent for PlusVibe. Follow the reasoning steps below when responding to the user.

Reasoning steps:
1. Check if the user is associated with more than one workspace:
    - If so, ask which workspace they mean.
    - If only one, use that one.
2. For email sending/warmup issues:
    - Pull their email account info with `get_user_email_accounts(user_id, workspace_id)`
    - Gather warmup progress and deliverability status.
3. Respond only based on info you have. Do not make up facts. If info is missing, ask user to elaborate.

First, walk through each step and display your reasoning.  
Then, compose your final reply to the user."""

    # The user message to test
    user_message = """can I launch a new campaign today?

please check how many days I warmed up so far as my emails were hitting the spam folder."""

    # Create the messages for OpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    print("=" * 80)
    print("TESTING CHAIN OF THOUGHT REASONING")
    print("=" * 80)
    print(f"System Prompt:")
    print(system_prompt)
    print("-" * 40)
    print(f"User Message:")
    print(user_message)
    print("=" * 80)
    print("Sending to OpenAI...")
    print()
    
    # Call OpenAI with retry logic
    response = call_openai_with_retry(
        messages=messages,
        max_completion_tokens=800,  # Allow for detailed reasoning
        temperature=0.3,  # Lower temperature for more consistent reasoning
        max_retries=3
    )
    
    if response is None:
        print("ERROR: OpenAI API call failed after all retries")
        return
    
    ai_response = response.choices[0].message.content.strip()
    
    print("OPENAI RESPONSE:")
    print("=" * 80)
    print(ai_response)
    print("=" * 80)
    
    # Also show token usage if available
    if hasattr(response, 'usage'):
        print(f"Token usage: {response.usage}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_reasoning_chain() 