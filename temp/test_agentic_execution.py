#!/usr/bin/env python3
"""
Test script for agentic execution - OpenAI executes steps until completion
Based on: https://cookbook.openai.com/examples/gpt4-1_prompting_guide
"""

import sys
import os
import json

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from openai_utils import call_openai_with_retry

class MockPlusVibeAPI:
    """Mock API to simulate PlusVibe functions"""
    
    def __init__(self):
        self.users = {
            "user_12345": {
                "workspaces": ["Marketing Team", "Sales Team"],
                "email_accounts": {
                    "Marketing Team": [
                        {"id": "email_1", "address": "john@company.com", "warmup_days": 14, "status": "good_deliverability"},
                        {"id": "email_2", "address": "support@company.com", "warmup_days": 7, "status": "spam_issues"}
                    ],
                    "Sales Team": [
                        {"id": "email_3", "address": "sales@company.com", "warmup_days": 21, "status": "excellent_deliverability"}
                    ]
                }
            }
        }
    
    def get_user_workspaces(self, user_id):
        """Get user's workspaces"""
        return self.users.get(user_id, {}).get("workspaces", [])
    
    def get_user_email_accounts(self, user_id, workspace_id):
        """Get email accounts for a workspace"""
        return self.users.get(user_id, {}).get("email_accounts", {}).get(workspace_id, [])
    
    def get_warmup_status(self, email_account_id):
        """Get detailed warmup status"""
        # Find the email account
        for user_data in self.users.values():
            for workspace_accounts in user_data["email_accounts"].values():
                for account in workspace_accounts:
                    if account["id"] == email_account_id:
                        return {
                            "warmup_days": account["warmup_days"],
                            "status": account["status"],
                            "recommendation": "ready_for_campaign" if account["warmup_days"] >= 14 and "good" in account["status"] else "continue_warmup"
                        }
        return None

# Global API instance
api = MockPlusVibeAPI()

def execute_function_call(function_name, arguments):
    """Execute a function call and return the result"""
    try:
        if function_name == "get_user_workspaces":
            return api.get_user_workspaces(arguments.get("user_id"))
        elif function_name == "get_user_email_accounts":
            return api.get_user_email_accounts(arguments.get("user_id"), arguments.get("workspace_id"))
        elif function_name == "get_warmup_status":
            return api.get_warmup_status(arguments.get("email_account_id"))
        else:
            return f"Error: Unknown function {function_name}"
    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"

def test_agentic_execution():
    """Test agentic execution where OpenAI executes steps until completion"""
    
    # System prompt with agentic instructions from GPT-4.1 guide
    system_prompt = """You are an agent for PlusVibe support - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.

If you are not sure about file content or codebase structure pertaining to the user's request, use your tools to read files and gather the relevant information: do NOT guess or make up an answer.

You MUST plan extensively before each function call, and reflect extensively on the outcomes of the previous function calls. DO NOT do this entire process by making function calls only, as this can impair your ability to solve the problem and think insightfully.

# Available Functions:
- get_user_workspaces(user_id): Returns list of user's workspaces
- get_user_email_accounts(user_id, workspace_id): Returns email accounts for a workspace  
- get_warmup_status(email_account_id): Returns detailed warmup status and recommendations

# Current Context:
- User ID: user_12345
- User is asking about campaign launch readiness and warmup status

# Your Task:
1. Gather all necessary information by calling the appropriate functions
2. Analyze the data thoroughly
3. Provide a complete, actionable recommendation
4. Do NOT stop until you have fully answered the user's question

IMPORTANT: When you want to call a function, format it as:
FUNCTION_CALL: function_name(arg1="value1", arg2="value2")

I will execute the function and give you the result, then you continue until the task is complete."""

    user_message = """can I launch a new campaign today?

please check how many days I warmed up so far as my emails were hitting the spam folder."""

    # Start the conversation
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    print("=" * 80)
    print("TESTING AGENTIC EXECUTION - OpenAI Executes Until Completion")
    print("=" * 80)
    print("User Query:", user_message)
    print("=" * 80)
    
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🤖 ITERATION {iteration}")
        print("-" * 40)
        
        # Get OpenAI response
        response = call_openai_with_retry(
            messages=messages,
            max_completion_tokens=800,
            temperature=0.1,
            max_retries=3
        )
        
        if response is None:
            print("ERROR: OpenAI API call failed")
            break
        
        ai_response = response.choices[0].message.content.strip()
        print("AI Response:")
        print(ai_response)
        
        # Add AI response to conversation
        messages.append({"role": "assistant", "content": ai_response})
        
        # Check if AI wants to call a function
        if "FUNCTION_CALL:" in ai_response:
            # Extract function call
            lines = ai_response.split('\n')
            function_line = None
            for line in lines:
                if line.strip().startswith("FUNCTION_CALL:"):
                    function_line = line.strip()[14:].strip()  # Remove "FUNCTION_CALL:"
                    break
            
            if function_line:
                print(f"\n🔧 EXECUTING: {function_line}")
                
                # Parse function call (simple parsing for demo)
                try:
                    if "get_user_workspaces(" in function_line:
                        result = execute_function_call("get_user_workspaces", {"user_id": "user_12345"})
                    elif "get_user_email_accounts(" in function_line:
                        # Extract workspace from function call
                        workspace = function_line.split('workspace_id="')[1].split('"')[0]
                        result = execute_function_call("get_user_email_accounts", {"user_id": "user_12345", "workspace_id": workspace})
                    elif "get_warmup_status(" in function_line:
                        # Extract email_account_id from function call
                        email_id = function_line.split('email_account_id="')[1].split('"')[0]
                        result = execute_function_call("get_warmup_status", {"email_account_id": email_id})
                    else:
                        result = "Error: Could not parse function call"
                    
                    print(f"📊 RESULT: {json.dumps(result, indent=2)}")
                    
                    # Add function result to conversation
                    function_result_message = f"Function result: {json.dumps(result, indent=2)}"
                    messages.append({"role": "user", "content": function_result_message})
                    
                except Exception as e:
                    error_msg = f"Error executing function: {str(e)}"
                    print(f"❌ ERROR: {error_msg}")
                    messages.append({"role": "user", "content": error_msg})
            
        else:
            # No function call - check if AI is done
            if any(phrase in ai_response.lower() for phrase in ["recommendation:", "conclusion:", "final answer:", "in summary:"]):
                print(f"\n✅ TASK COMPLETED in {iteration} iterations!")
                break
            else:
                # AI might need more guidance
                messages.append({"role": "user", "content": "Please continue with your analysis or call the necessary functions to complete the task."})
    
    if iteration >= max_iterations:
        print(f"\n⚠️ Reached maximum iterations ({max_iterations})")
    
    print("\n" + "=" * 80)
    print("FINAL CONVERSATION SUMMARY:")
    print("=" * 80)
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and not msg["content"].startswith("Function result:"):
            print(f"👤 User: {msg['content'][:100]}...")
        elif msg["role"] == "assistant":
            print(f"🤖 AI: {msg['content'][:100]}...")

if __name__ == "__main__":
    test_agentic_execution() 