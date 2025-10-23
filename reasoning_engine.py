"""
Shared Reasoning Engine
Supports both playbook-driven and self-thinking step-by-step reasoning
"""

import openai_utils
import config
from assistant_functions import get_functions_documentation, execute_function


class ReasoningEngine:
    """Shared reasoning engine for step-by-step problem solving"""
    
    def __init__(self, assistant_name="Assistant"):
        self.assistant_name = assistant_name
        self.functions_doc = get_functions_documentation()
    
    def execute_reasoning(self, 
                         query, 
                         context_data=None,
                         playbook=None, 
                         max_iterations=5,
                         mode="self_thinking"):
        """
        Execute reasoning process with explicit goal tracking
        
        Args:
            query: The question/task to solve
            context_data: Additional context (user_email, conversation_id, etc.)
            playbook: Optional predefined steps (for playbook mode)
            max_iterations: Max reasoning iterations
            mode: "playbook" or "self_thinking"
        
        Returns:
            Final answer and reasoning trace
        """
        
        # Define explicit goal from the query
        goal_definition = self._extract_goal_from_query(query)
        
        if mode == "playbook" and playbook:
            return self._execute_playbook_reasoning(query, context_data, playbook, max_iterations, goal_definition)
        else:
            return self._execute_self_thinking_reasoning(query, context_data, max_iterations, goal_definition)
    
    def _execute_playbook_reasoning(self, query, context_data, playbook, max_iterations, goal_definition):
        """Execute reasoning following a predefined playbook"""
        
        system_prompt = f"""You are {self.assistant_name}, following a step-by-step playbook to solve problems.

PLAYBOOK STEPS:
{self._format_playbook_steps(playbook)}

INSTRUCTIONS:
- Follow the playbook steps in order
- For each step, determine what information you need
- Call functions to gather required data
- Mark each step as COMPLETED when done
- If a step reveals the problem, you can stop early
- Provide clear reasoning for each step

AVAILABLE FUNCTIONS:
{self._format_functions_for_ai()}

Context: {context_data or 'None'}
"""
        
        return self._reasoning_loop(query, system_prompt, max_iterations, goal_definition, playbook_mode=True)
    
    def _execute_self_thinking_reasoning(self, query, context_data, max_iterations, goal_definition):
        """Execute reasoning where AI creates its own steps"""
        
        system_prompt = f"""You are {self.assistant_name}, solving problems step-by-step with immediate action.

CRITICAL RULES:
- When you need data, call functions IMMEDIATELY using: FUNCTION_CALL: function_name(param="value")
- Don't just talk about calling functions - ACTUALLY CALL THEM
- Be concise - take action, don't write essays
- Stop when you have the answer

AVAILABLE FUNCTIONS:
{self._format_functions_for_ai()}

Context: {context_data or 'None'}

Example of CORRECT behavior:
User: "What's the workspace ID?"
You: "I'll check the user plan to get the workspace ID. FUNCTION_CALL: check_user_plan(user_email="user@example.com")"
[After getting results]: "The workspace ID is 12345."

Example of WRONG behavior:
You: "STEP 1: I need to check the user plan. STEP 2: I will call the function..." (TOO VERBOSE - JUST DO IT!)
"""
        
        return self._reasoning_loop(query, system_prompt, max_iterations, goal_definition, playbook_mode=False)
    
    def _reasoning_loop(self, query, system_prompt, max_iterations, goal_definition, playbook_mode=False):
        """Core reasoning loop with goal tracking"""
        
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {query}\n\nBegin your step-by-step reasoning."}
        ]
        
        reasoning_trace = []
        
        try:
            for iteration in range(max_iterations):
                print(f"DEBUG: Reasoning iteration {iteration + 1}/{max_iterations}")
                
                # Safety check - if we're on last iteration, force a conclusion
                if iteration == max_iterations - 1:
                    print("DEBUG: Final iteration - forcing conclusion")
                
                # Call OpenAI
                response_obj = openai_utils.call_openai_with_retry(
                    messages=conversation_history,
                    max_completion_tokens=1000,
                    temperature=0.7
                )
                
                if not response_obj or not response_obj.choices:
                    return {
                        "answer": "I'm having trouble connecting to the AI service.",
                        "reasoning_trace": reasoning_trace,
                        "success": False
                    }
                
                response = response_obj.choices[0].message.content
                reasoning_trace.append(f"Iteration {iteration + 1}: {response}")
                
                print(f"DEBUG: AI Response: {response[:200]}...")
                
                # Extract and execute function calls
                function_calls = self._extract_function_calls(response)
                
                if function_calls:
                    # Execute functions
                    function_results = {}
                    
                    for func_name, params in function_calls:
                        try:
                            print(f"DEBUG: Executing function: {func_name}({params})")
                            result = execute_function(func_name, **params)
                            formatted_result = self._format_function_result(func_name, result)
                            function_results[func_name] = formatted_result
                        except Exception as e:
                            function_results[func_name] = f"Error: {str(e)}"
                    
                    # Continue conversation
                    conversation_history.append({"role": "assistant", "content": response})
                    
                    results_text = "\n".join([f"{func}: {result}" for func, result in function_results.items()])
                    conversation_history.append({
                        "role": "user", 
                        "content": f"Function results:\n{results_text}\n\nContinue with next step or provide final answer."
                    })
                    
                else:
                    # No function calls = check goal completion
                    if self._check_goal_completion(goal_definition, response, conversation_history):
                        print(f"DEBUG: Goal completed in iteration {iteration + 1}")
                        return {
                            "answer": response,
                            "reasoning_trace": reasoning_trace,
                            "success": True,
                            "iterations_used": iteration + 1
                        }
                    else:
                        # Continue reasoning without function calls
                        conversation_history.append({"role": "assistant", "content": response})
                        conversation_history.append({
                            "role": "user", 
                            "content": "Continue with your next step."
                        })
            
            # Max iterations reached
            return {
                "answer": f"Reasoning completed after {max_iterations} steps. Current conclusion: {response}",
                "reasoning_trace": reasoning_trace,
                "success": False,
                "iterations_used": max_iterations
            }
            
        except Exception as e:
            print(f"Error in reasoning loop: {e}")
            return {
                "answer": f"Error during reasoning: {str(e)}",
                "reasoning_trace": reasoning_trace,
                "success": False
            }
    
    def _extract_function_calls(self, response_text):
        """Extract function calls from AI response"""
        import re
        
        function_calls = []
        
        # Pattern 1: FUNCTION_CALL: format
        function_call_pattern = r'FUNCTION_CALL:\s*(\w+)\((.*?)\)'
        matches = re.findall(function_call_pattern, response_text)
        
        for func_name, params_str in matches:
            try:
                params = {}
                if params_str.strip():
                    param_pairs = re.findall(r'(\w+)="([^"]*)"', params_str)
                    params = {key: value for key, value in param_pairs}
                
                function_calls.append((func_name, params))
            except Exception as e:
                print(f"Error parsing function call {func_name}: {e}")
        
        # Pattern 2: Code blocks with function calls (simpler pattern)
        code_block_pattern = r'```(?:python|)\s*(\w+)\s*\(\s*(.*?)\s*\)\s*```'
        code_matches = re.findall(code_block_pattern, response_text, re.DOTALL)
        
        for func_name, params_str in code_matches:
            # Only process known function names
            known_functions = ['check_user_plan', 'get_campaigns', 'get_email_accounts', 'check_account_health']
            if func_name in known_functions:
                try:
                    params = {}
                    if params_str.strip():
                        # Clean up the params string
                        params_clean = params_str.replace('\n', '').strip()
                        param_pairs = re.findall(r'(\w+)="([^"]*)"', params_clean)
                        params = {key: value for key, value in param_pairs}
                    
                    function_calls.append((func_name, params))
                    print(f"DEBUG: Extracted function call from code block: {func_name}({params})")
                except Exception as e:
                    print(f"Error parsing code block function call {func_name}: {e}")
        
        return function_calls
    
    def _extract_goal_from_query(self, query):
        """Extract explicit goal definition from user query using fast model"""
        try:
            goal_prompt = f"""Extract the specific goal/objective from this query in a clear, measurable format.

Query: "{query}"

Return ONLY the goal definition as a short sentence. Examples:
- "Find the workspace ID for a specific workspace name"  
- "Get all workspace IDs that a user has access to"
- "Diagnose why a campaign is not sending emails"

Goal:"""

            print(f"DEBUG: Goal extraction query: '{query}'")
            print(f"DEBUG: Goal extraction prompt: {goal_prompt}")
            
            response_obj = openai_utils.call_openai_with_retry(
                messages=[{"role": "user", "content": goal_prompt}],
                max_completion_tokens=100,
                temperature=0.1,
                model=config.FAST  # Use fast model for goal extraction
            )
            
            if response_obj and response_obj.choices:
                goal = response_obj.choices[0].message.content.strip()
                print(f"DEBUG: Raw goal response: '{goal}'")
                print(f"DEBUG: Extracted goal: '{goal}'")
                return goal
            else:
                print("DEBUG: No response from goal extraction")
            
        except Exception as e:
            print(f"Error extracting goal: {e}")
        
        # Fallback to original query
        print(f"DEBUG: Using fallback goal: '{query}'")
        return query
    
    def _check_goal_completion(self, goal_definition, current_response, conversation_history):
        """Check if the goal has been achieved using fast model"""
        try:
            # Build context from conversation
            context_summary = ""
            if len(conversation_history) > 2:
                # Get last few exchanges for context
                recent_context = conversation_history[-4:]  # Last 2 exchanges
                context_lines = []
                for msg in recent_context:
                    role = msg['role'].upper()
                    content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                    context_lines.append(f"{role}: {content}")
                context_summary = "\n".join(context_lines)
            
            completion_prompt = f"""Determine if the goal has been fully achieved based on the current response and context.

GOAL: {goal_definition}

RECENT CONTEXT:
{context_summary}

CURRENT RESPONSE: {current_response}

Has the goal been fully achieved? Answer ONLY "YES" or "NO" with brief reasoning.

Answer:"""

            print(f"DEBUG: Goal completion check prompt:")
            print(f"  GOAL: {goal_definition}")
            print(f"  CURRENT RESPONSE: {current_response[:200]}...")
            
            response_obj = openai_utils.call_openai_with_retry(
                messages=[{"role": "user", "content": completion_prompt}],
                max_completion_tokens=50,
                temperature=0.1,
                model=config.FAST  # Use fast model for goal completion
            )
            
            if response_obj and response_obj.choices:
                result = response_obj.choices[0].message.content.strip().lower()
                is_complete = result.startswith("yes")
                print(f"DEBUG: Goal completion raw response: '{result}'")
                print(f"DEBUG: Goal completion check: {result} -> {is_complete}")
                return is_complete
            else:
                print("DEBUG: No response from goal completion check")
            
        except Exception as e:
            print(f"Error checking goal completion: {e}")
        
        # Fallback: not complete
        return False
    
    def _format_playbook_steps(self, playbook):
        """Format playbook steps for AI"""
        if isinstance(playbook, list):
            return "\n".join([f"STEP {i+1}: {step}" for i, step in enumerate(playbook)])
        elif isinstance(playbook, dict):
            return "\n".join([f"STEP {i+1}: {step['description']}" for i, step in enumerate(playbook.get('steps', []))])
        else:
            return str(playbook)
    
    def _format_functions_for_ai(self):
        """Format available functions for AI"""
        sections_text = []
        
        for section_name, section_data in self.functions_doc.get('sections', {}).items():
            sections_text.append(f"\n## {section_name.upper()}")
            
            for func in section_data.get('functions', []):
                sections_text.append(f"\n### {func['name']}")
                sections_text.append(f"Description: {func['description']}")
                sections_text.append("Inputs:")
                for param, details in func.get('inputs', {}).items():
                    required = " (required)" if details.get('required', False) else " (optional)"
                    sections_text.append(f"  - {param}: {details.get('description', '')}{required}")
        
        return "\n".join(sections_text)
    
    def _format_function_result(self, func_name, result):
        """Format function results"""
        # Import the existing formatter from assistant processor
        try:
            from assistant_processor import assistant_processor
            return assistant_processor._format_function_result(func_name, result)
        except:
            # Fallback formatting - NO TRIMMING for check_user_plan
            if isinstance(result, dict) and 'error' in result:
                return f"Error: {result['error']}"
            elif func_name == "check_user_plan":
                # Never trim user plan results
                return str(result)
            else:
                return str(result)[:200] + "..." if len(str(result)) > 200 else str(result)


# Global instance
reasoning_engine = ReasoningEngine()