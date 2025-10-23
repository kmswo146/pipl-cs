"""
OpenAI utility functions with retry logic
"""

import openai
import config
import time
import random

# Set up Azure OpenAI client
openai_client = openai.AzureOpenAI(
    api_key=config.AZURE_OPENAI_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT
)

def call_openai_with_retry(messages, max_completion_tokens=300, temperature=0.7, response_format=None, max_retries=3, model=None):
    """
    Call OpenAI API with retry logic
    
    Args:
        messages: List of message objects for the API
        max_completion_tokens: Maximum tokens to generate
        temperature: Temperature for response generation (ignored for models that don't support it)
        response_format: Optional response format (e.g., {"type": "json_object"})
        max_retries: Maximum number of retry attempts
        model: Model to use (defaults to config.DEFAULT_MODEL)
    
    Returns:
        OpenAI response object or None if all retries failed
    """
    
    # Models that don't support custom temperature
    no_temp_models = ['gpt-5-mini', 'gpt-5-nano']
    
    for attempt in range(max_retries):
        try:
            print(f"DEBUG: OpenAI API call attempt {attempt + 1}/{max_retries}")
            
            # Prepare API call parameters
            selected_model = model or config.DEFAULT_MODEL
            api_params = {
                "model": selected_model,
                "messages": messages,
                "max_completion_tokens": max_completion_tokens
            }
            
            # Only add temperature for models that support it
            if selected_model not in no_temp_models:
                api_params["temperature"] = temperature
            
            # Add response format if specified
            if response_format:
                api_params["response_format"] = response_format
            
            # Make the API call
            response = openai_client.chat.completions.create(**api_params)
            
            print(f"DEBUG: OpenAI API call successful on attempt {attempt + 1}")
            return response
            
        except openai.RateLimitError as e:
            print(f"RETRY: Rate limit error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter for rate limits
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"RETRY: Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Rate limit exceeded after {max_retries} attempts")
                return None
                
        except openai.APITimeoutError as e:
            print(f"RETRY: Timeout error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                # Shorter wait for timeout errors
                wait_time = 2 + random.uniform(0, 1)
                print(f"RETRY: Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Timeout after {max_retries} attempts")
                return None
                
        except openai.APIConnectionError as e:
            print(f"RETRY: Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                # Wait longer for connection issues
                wait_time = 5 + random.uniform(0, 2)
                print(f"RETRY: Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Connection failed after {max_retries} attempts")
                return None
                
        except openai.AuthenticationError as e:
            print(f"ERROR: Authentication error (no retry): {e}")
            return None
            
        except openai.BadRequestError as e:
            print(f"ERROR: Bad request error (no retry): {e}")
            return None
            
        except Exception as e:
            print(f"RETRY: Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                # Generic wait for unexpected errors
                wait_time = 3 + random.uniform(0, 1)
                print(f"RETRY: Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: Unexpected error after {max_retries} attempts")
                return None
    
    return None 