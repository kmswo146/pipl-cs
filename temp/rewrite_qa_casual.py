#!/usr/bin/env python3
"""
Rewrite QA answers to be more casual and human-like
"""

import json
import random
import re
import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from openai_utils import call_openai_with_retry

def maybe_lowercase_first_word(text, prob=0.3):
    """Randomly lowercase the first word if it's capitalized (but not 'I')"""
    match = re.match(r"([A-Z][a-z']*)(\b.*)", text)
    if match and random.random() < prob and match.group(1) != "I":
        return match.group(1).lower() + match.group(2)
    return text

def remove_commas_from_numbers(text):
    """Replace numbers like 1,000 or 2,500,000 with 1000 or 2500000"""
    return re.sub(r'(\d{1,3}(?:,\d{3})+)', lambda m: m.group(0).replace(',', ''), text)

def rewrite_casual(answer):
    """Use OpenAI to rewrite the answer in a more casual, human style"""
    prompt = (
        "Rewrite the following customer support answer to sound more casual and human-typed. "
        "Make it less formal and AI-like. Use contractions, simpler words, and a friendly tone. "
        "Keep all the important information and meaning exactly the same. "
        "Don't add extra information or change any facts. "
        "Make it sound like a helpful person typing a quick response:\n\n"
        f"{answer}\n\n"
        "Return only the rewritten answer, nothing else."
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful, casual customer support person who types in a friendly, natural way."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = call_openai_with_retry(
            messages=messages, 
            max_completion_tokens=400, 
            temperature=0.7,
            max_retries=3
        )
        
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            rewritten = response.choices[0].message.content.strip()
            # Remove any quotes that might wrap the response
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            return rewritten
        else:
            print(f"WARNING: No response from OpenAI, keeping original answer")
            return answer
            
    except Exception as e:
        print(f"ERROR rewriting answer: {e}")
        return answer

def process_qa_file(input_path, output_path, rewrite_prob=0.4):
    """Process the QA file and rewrite answers"""
    print(f"Loading QA file from: {input_path}")
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR loading file: {e}")
        return
    
    qa_candidates = data.get("qa_candidates", [])
    total_count = len(qa_candidates)
    print(f"Found {total_count} QA pairs to process")
    
    for i, qa in enumerate(qa_candidates, 1):
        print(f"\nProcessing {i}/{total_count}: {qa['question'][:60]}...")
        
        original_answer = qa["answer"]
        
        # Step 1: Maybe lowercase first word randomly
        if random.random() < rewrite_prob:
            qa["answer"] = maybe_lowercase_first_word(qa["answer"])
            if qa["answer"] != original_answer:
                print(f"  → Lowercased first word")
        
        # Step 2: Always remove commas from numbers
        before_numbers = qa["answer"]
        qa["answer"] = remove_commas_from_numbers(qa["answer"])
        if qa["answer"] != before_numbers:
            print(f"  → Removed commas from numbers")
        
        # Step 3: Always rewrite to casual style
        print(f"  → Rewriting with OpenAI...")
        qa["answer"] = rewrite_casual(qa["answer"])
        
        print(f"  ✓ Completed")
    
    # Save the updated data
    print(f"\nSaving updated QA file to: {output_path}")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Successfully saved {total_count} rewritten QA pairs!")
    except Exception as e:
        print(f"ERROR saving file: {e}")

def main():
    """Main function"""
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "qa_candidates_filtered.json")
    output_path = os.path.join(script_dir, "qa_candidates_filtered_casual.json")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        return
    
    print("=== QA Answer Rewriter ===")
    print("This script will:")
    print("1. Randomly lowercase some first words")
    print("2. Remove commas from numbers (1,000 → 1000)")
    print("3. Rewrite answers to be more casual and human-like")
    print()
    
    # Process the file
    process_qa_file(input_path, output_path)

if __name__ == "__main__":
    main() 