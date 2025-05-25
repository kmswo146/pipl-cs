#!/usr/bin/env python3
"""
Extract Q&A pairs from conversation history using OpenAI
Processes conversations_for_llm.json and creates a knowledge base
"""

import sys
import os
import json
from datetime import datetime
import re

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from openai_utils import call_openai_with_retry

class QAExtractor:
    def __init__(self):
        self.qa_candidates = []
        self.processed_count = 0
        self.suitable_count = 0
        
    def load_conversations(self, filename="conversations_for_llm.json"):
        """Load conversations from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            print(f"Loaded {len(conversations)} conversations")
            return conversations
        except Exception as e:
            print(f"Error loading conversations: {e}")
            return []
    
    def is_suitable_qa_candidate(self, conversation):
        """Check if conversation contains suitable Q&A pair"""
        try:
            # Build conversation text
            conv_text = ""
            for msg in conversation['messages']:
                role = "Customer" if msg['role'] == 'user' else "Support"
                conv_text += f"{role}: {msg['text']}\n"
            
            prompt = """Analyze this customer support conversation to determine if it contains a suitable Q&A pair for a knowledge base.

A suitable Q&A pair must have:
1. A clear, specific question from the customer
2. A helpful, complete answer from support
3. General applicability (not user-specific account details)
4. Complete resolution (not just "let me check" or "we'll get back to you")

Return JSON format:
{"suitable": true/false, "reason": "explanation", "confidence": 0.0-1.0}"""

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Conversation:\n{conv_text}"}
            ]
            
            response = call_openai_with_retry(
                messages=messages,
                max_completion_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"},
                max_retries=3
            )
            
            if response is None:
                print("ERROR: OpenAI API call failed for suitability check")
                return False, 0.0, "API call failed"
            
            result = json.loads(response.choices[0].message.content)
            return result.get('suitable', False), result.get('confidence', 0.0), result.get('reason', '')
            
        except Exception as e:
            print(f"Error checking suitability: {e}")
            return False, 0.0, "Error in processing"
    
    def extract_qa_pair(self, conversation):
        """Extract normalized Q&A pair from conversation"""
        try:
            # Build conversation text
            conv_text = ""
            for msg in conversation['messages']:
                role = "Customer" if msg['role'] == 'user' else "Support"
                conv_text += f"{role}: {msg['text']}\n"
            
            prompt = """Extract a clean Q&A pair from this customer support conversation.

Requirements:
1. Normalize the question (remove user-specific details, standardize phrasing)
2. Extract the most helpful, complete answer
3. Make it generally applicable to other users

Return JSON format:
{
  "question": "normalized question",
  "answer": "complete answer", 
  "topic": "main topic/category",
  "quality_score": 1-10
}"""

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Conversation:\n{conv_text}"}
            ]
            
            response = call_openai_with_retry(
                messages=messages,
                max_completion_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"},
                max_retries=3
            )
            
            if response is None:
                print("ERROR: OpenAI API call failed for Q&A extraction")
                return None
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error extracting Q&A: {e}")
            return None
    
    def find_similar_qa(self, new_qa):
        """Find similar Q&A in existing candidates"""
        if not self.qa_candidates:
            return None, 0.0
        
        try:
            # Build existing Q&As text
            existing_qas = ""
            for i, qa in enumerate(self.qa_candidates):
                existing_qas += f"{i+1}. Q: {qa['question']}\n   A: {qa['answer'][:100]}...\n\n"
            
            prompt = """Compare this new Q&A against existing Q&As to find similarities.

Return JSON format:
{
  "most_similar_index": number (1-based index, 0 if no similarity),
  "similarity_score": 0.0-1.0,
  "action": "same|merge|new",
  "reason": "explanation"
}

Similarity guidelines:
- >0.9: Same question (increment count)
- 0.7-0.9: Very similar (suggest merge)
- <0.7: Different (add as new)"""

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""New Q&A:
Q: {new_qa['question']}
A: {new_qa['answer']}

Existing Q&As:
{existing_qas}"""}
            ]
            
            response = call_openai_with_retry(
                messages=messages,
                max_completion_tokens=300,
                temperature=0.1,
                response_format={"type": "json_object"},
                max_retries=3
            )
            
            if response is None:
                print("ERROR: OpenAI API call failed for similarity check")
                return None, 0.0
            
            result = json.loads(response.choices[0].message.content)
            similar_index = result.get('most_similar_index', 0)
            similarity = result.get('similarity_score', 0.0)
            
            if similar_index > 0 and similar_index <= len(self.qa_candidates):
                return self.qa_candidates[similar_index - 1], similarity
            
            return None, similarity
            
        except Exception as e:
            print(f"Error finding similar Q&A: {e}")
            return None, 0.0
    
    def add_or_merge_qa(self, new_qa, conversation_id):
        """Add new Q&A or merge with existing similar one"""
        similar_qa, similarity = self.find_similar_qa(new_qa)
        
        if similar_qa and similarity > 0.9:
            # Same question - increment count
            similar_qa['count'] += 1
            similar_qa['conversation_ids'].append(conversation_id)
            print(f"  → Incremented count for similar Q&A (similarity: {similarity:.2f})")
            
        elif similar_qa and similarity > 0.7:
            # Very similar - suggest merge (for now, just increment)
            similar_qa['count'] += 1
            similar_qa['conversation_ids'].append(conversation_id)
            similar_qa['similar_questions'].append(new_qa['question'])
            print(f"  → Added as similar question (similarity: {similarity:.2f})")
            
        else:
            # New Q&A
            qa_entry = {
                "question": new_qa['question'],
                "answer": new_qa['answer'],
                "topic": new_qa.get('topic', 'General'),
                "count": 1,
                "quality_score": new_qa.get('quality_score', 5),
                "conversation_ids": [conversation_id],
                "similar_questions": [],
                "created_at": datetime.now().isoformat()
            }
            self.qa_candidates.append(qa_entry)
            print(f"  → Added as new Q&A")
    
    def process_conversations(self):
        """Main processing function"""
        conversations = self.load_conversations()
        
        if not conversations:
            print("No conversations to process")
            return
        
        print(f"Processing {len(conversations)} conversations...")
        print("=" * 60)
        
        for i, conv in enumerate(conversations):
            conv_id = conv.get('id', f'conv_{i}')
            self.processed_count += 1
            
            print(f"[{self.processed_count}/{len(conversations)}] Processing conversation {conv_id}")
            
            # Check if suitable for Q&A
            is_suitable, confidence, reason = self.is_suitable_qa_candidate(conv)
            
            if not is_suitable:
                print(f"  ✗ Not suitable: {reason}")
                continue
            
            self.suitable_count += 1
            print(f"  ✓ Suitable (confidence: {confidence:.2f}): {reason}")
            
            # Extract Q&A pair
            qa_pair = self.extract_qa_pair(conv)
            if not qa_pair:
                print(f"  ✗ Failed to extract Q&A")
                continue
            
            print(f"  Q: {qa_pair['question'][:80]}...")
            
            # Add or merge with existing
            self.add_or_merge_qa(qa_pair, conv_id)
            
            print()
        
        self.save_results()
    
    def save_results(self):
        """Save extracted Q&A candidates to file"""
        # Sort by count (most popular first)
        sorted_qas = sorted(self.qa_candidates, key=lambda x: x['count'], reverse=True)
        
        output = {
            "summary": {
                "total_conversations": self.processed_count,
                "suitable_conversations": self.suitable_count,
                "unique_qa_pairs": len(self.qa_candidates),
                "generated_at": datetime.now().isoformat()
            },
            "qa_candidates": sorted_qas
        }
        
        filename = f"qa_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total conversations processed: {self.processed_count}")
        print(f"Suitable for Q&A: {self.suitable_count}")
        print(f"Unique Q&A pairs extracted: {len(self.qa_candidates)}")
        print(f"Results saved to: {filename}")
        print()
        print("Top Q&A pairs by popularity:")
        for i, qa in enumerate(sorted_qas[:5]):
            print(f"{i+1}. [{qa['count']}x] {qa['question'][:60]}...")

def main():
    extractor = QAExtractor()
    extractor.process_conversations()

if __name__ == "__main__":
    main() 