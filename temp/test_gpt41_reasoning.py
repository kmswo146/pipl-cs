#!/usr/bin/env python3
"""
Test script using GPT-4.1 specific prompting techniques
Based on: https://cookbook.openai.com/examples/gpt4-1_prompting_guide
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from openai_utils import call_openai_with_retry

def test_gpt41_reasoning():
    """Test GPT-4.1 specific reasoning capabilities"""
    
    # Enhanced system prompt using GPT-4.1 techniques
    system_prompt = """You are a support agent for PlusVibe (cold email automation SaaS). 

CRITICAL: You MUST plan extensively before responding, and reflect on each step. DO NOT skip the reasoning process.

# Workflow Instructions:
1. **Planning Phase**: Explicitly plan your approach step-by-step
2. **Information Gathering**: Identify what information you have vs. what you need
3. **Reasoning Phase**: Walk through your logic for each decision
4. **Response Composition**: Craft your final response based on your analysis

# Support Process:
1. **Workspace Identification**: 
   - Check if user has multiple workspaces
   - If multiple: ask which workspace
   - If single: proceed with that workspace

2. **Email Account Analysis** (for warmup/sending issues):
   - Use `get_user_email_accounts(user_id, workspace_id)` to get account info
   - Check warmup progress and deliverability status
   - Analyze spam folder issues

3. **Response Guidelines**:
   - Only state facts you can verify
   - If information is missing, explicitly ask for it
   - Be specific about what you need to help

IMPORTANT: You must show your complete reasoning process before giving your final answer. Think step by step and be thorough in your analysis."""

    # Test scenario
    user_message = """can I launch a new campaign today?

please check how many days I warmed up so far as my emails were hitting the spam folder."""

    # Create the messages for OpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    print("=" * 80)
    print("TESTING GPT-4.1 ENHANCED REASONING")
    print("=" * 80)
    print("Using techniques from: https://cookbook.openai.com/examples/gpt4-1_prompting_guide")
    print()
    print("Key GPT-4.1 Features Being Tested:")
    print("✓ Explicit planning and reflection")
    print("✓ Step-by-step reasoning")
    print("✓ Literal instruction following")
    print("✓ Structured workflow adherence")
    print("=" * 80)
    print("Sending to OpenAI...")
    print()
    
    # Call OpenAI with retry logic
    response = call_openai_with_retry(
        messages=messages,
        max_completion_tokens=1000,  # More tokens for detailed reasoning
        temperature=0.1,  # Very low temperature for consistent reasoning
        max_retries=3
    )
    
    if response is None:
        print("ERROR: OpenAI API call failed after all retries")
        return
    
    ai_response = response.choices[0].message.content.strip()
    
    print("GPT-4.1 RESPONSE:")
    print("=" * 80)
    print(ai_response)
    print("=" * 80)
    
    # Analyze the response quality
    print("\nRESPONSE ANALYSIS:")
    print("-" * 40)
    
    # Check if it followed the workflow
    has_planning = "plan" in ai_response.lower() or "step" in ai_response.lower()
    has_reasoning = "reasoning" in ai_response.lower() or "analysis" in ai_response.lower()
    mentions_workspace = "workspace" in ai_response.lower()
    mentions_email_accounts = "email" in ai_response.lower() and "account" in ai_response.lower()
    asks_for_info = "?" in ai_response
    
    print(f"✓ Shows planning/steps: {'YES' if has_planning else 'NO'}")
    print(f"✓ Includes reasoning: {'YES' if has_reasoning else 'NO'}")
    print(f"✓ Addresses workspace: {'YES' if mentions_workspace else 'NO'}")
    print(f"✓ Mentions email accounts: {'YES' if mentions_email_accounts else 'NO'}")
    print(f"✓ Asks for missing info: {'YES' if asks_for_info else 'NO'}")
    
    # Show token usage
    if hasattr(response, 'usage'):
        print(f"\nToken usage: {response.usage}")
    
    print("\nTest completed successfully!")

def test_with_simulated_data():
    """Test with simulated workspace and email data"""
    
    system_prompt = """You are a support agent for PlusVibe. You have access to user data.

WORKFLOW: Plan → Analyze → Respond

# Available Functions (simulated):
- get_user_workspaces(user_id) → returns list of workspaces
- get_user_email_accounts(user_id, workspace_id) → returns email account details
- get_warmup_status(email_account_id) → returns warmup progress

# Current User Context:
- User ID: user_12345
- Workspaces: ["Marketing Team", "Sales Team"] 
- Email accounts in "Marketing Team": 
  - john@company.com (warmup: 14 days, status: "good deliverability")
  - support@company.com (warmup: 7 days, status: "spam issues detected")

INSTRUCTIONS: Use this data to provide specific, actionable advice. Show your reasoning process."""

    user_message = """can I launch a new campaign today?

please check how many days I warmed up so far as my emails were hitting the spam folder."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    print("\n" + "=" * 80)
    print("TESTING WITH SIMULATED DATA")
    print("=" * 80)
    
    response = call_openai_with_retry(
        messages=messages,
        max_completion_tokens=800,
        temperature=0.1,
        max_retries=3
    )
    
    if response:
        print("GPT-4.1 RESPONSE WITH DATA:")
        print("=" * 80)
        print(response.choices[0].message.content.strip())
        print("=" * 80)

if __name__ == "__main__":
    test_gpt41_reasoning()
    test_with_simulated_data() 