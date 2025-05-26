#!/usr/bin/env python3
"""
Insert QA entries from JSON file into MongoDB dashboard database
"""

import json
import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import config

def connect_to_dashboard_db():
    """Connect to the dashboard MongoDB database"""
    try:
        client = MongoClient(config.DASHBOARD_DB_URI)
        db = client.get_default_database()
        print(f"✓ Connected to dashboard database")
        return db
    except Exception as e:
        print(f"ERROR connecting to database: {e}")
        return None

def format_answer_as_html(answer):
    """Convert plain text answer to HTML format with paragraphs"""
    # Split by double newlines for paragraphs
    paragraphs = answer.split('\n\n')
    
    html_parts = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            # Check if it contains URLs and format them
            if 'http' in paragraph:
                # Simple URL detection and formatting
                import re
                url_pattern = r'(https?://[^\s]+)'
                paragraph = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', paragraph)
            
            html_parts.append(f"<p>{paragraph}</p>")
    
    return ''.join(html_parts)

def create_qa_entry(question, answer):
    """Create a QA entry in the MongoDB format"""
    current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    return {
        "_id": ObjectId(),
        "question": question.strip(),
        "answer": format_answer_as_html(answer),
        "createdAt": current_time,
        "updatedAt": current_time
    }

def insert_qa_entries(input_file_path, dry_run=True):
    """Insert QA entries from JSON file into dashboard database"""
    
    # Load the QA data
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR loading QA file: {e}")
        return
    
    qa_candidates = data.get("qa_candidates", [])
    total_count = len(qa_candidates)
    print(f"Found {total_count} QA pairs to process")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No data will be inserted")
        print("Set dry_run=False to actually insert data")
    
    # Connect to database
    if not dry_run:
        db = connect_to_dashboard_db()
        if db is None:
            return
        qa_collection = db.qa_entries
    
    # Process each QA pair
    inserted_count = 0
    skipped_count = 0
    
    for i, qa in enumerate(qa_candidates, 1):
        question = qa.get('question', '').strip()
        answer = qa.get('answer', '').strip()
        
        if not question or not answer:
            print(f"⚠️  Skipping {i}/{total_count}: Missing question or answer")
            skipped_count += 1
            continue
        
        # Create the entry
        entry = create_qa_entry(question, answer)
        
        if dry_run:
            print(f"\n📝 Would insert {i}/{total_count}:")
            print(f"   Question: {question[:80]}...")
            print(f"   Answer: {entry['answer'][:100]}...")
            print(f"   ID: {entry['_id']}")
        else:
            try:
                # Check if similar question already exists
                existing = qa_collection.find_one({"question": {"$regex": f"^{question}$", "$options": "i"}})
                if existing:
                    print(f"⚠️  Skipping {i}/{total_count}: Question already exists")
                    skipped_count += 1
                    continue
                
                # Insert the entry
                result = qa_collection.insert_one(entry)
                print(f"✓ Inserted {i}/{total_count}: {result.inserted_id}")
                inserted_count += 1
                
            except Exception as e:
                print(f"❌ Error inserting {i}/{total_count}: {e}")
                skipped_count += 1
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total QA pairs: {total_count}")
    if dry_run:
        print(f"Would insert: {total_count - skipped_count}")
        print(f"Would skip: {skipped_count}")
    else:
        print(f"Successfully inserted: {inserted_count}")
        print(f"Skipped: {skipped_count}")

def main():
    """Main function"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "qa_candidates_filtered_casual.json")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run the rewrite_qa_casual.py script first to generate the casual QA file.")
        return
    
    print("=== QA Dashboard Inserter ===")
    print(f"Input file: {input_file}")
    print(f"Database: {config.DASHBOARD_DB_URI}")
    print()
    
    # Ask user for confirmation
    print("Choose mode:")
    print("1. Dry run (preview only)")
    print("2. Actually insert data")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            insert_qa_entries(input_file, dry_run=True)
        elif choice == "2":
            confirm = input("Are you sure you want to insert data? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                insert_qa_entries(input_file, dry_run=False)
            else:
                print("Operation cancelled.")
        else:
            print("Invalid choice. Please run again and select 1 or 2.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 