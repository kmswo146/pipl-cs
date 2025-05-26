import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

# Load environment variables
load_dotenv()

DASHBOARD_DB_URI = os.getenv('DASHBOARD_DB_URI')
print(f"MongoDB URI: {DASHBOARD_DB_URI}")

try:
    # Set up MongoDB client
    mongo_client = MongoClient(DASHBOARD_DB_URI)
    db = mongo_client.get_default_database()
    qa_collection = db.qa_entries
    
    print("MongoDB connection successful!")
    
    # Test fetching the specific document
    doc = qa_collection.find_one({"_id": ObjectId("6832d2d44284c30bb33e46a5")})
    
    if doc:
        print("Document found!")
        print(f"Question: {doc.get('question')}")
        print(f"Answer: {doc.get('answer')}")
    else:
        print("Document not found!")
        
        # Let's see what documents exist
        print("Available documents:")
        for doc in qa_collection.find().limit(5):
            print(f"ID: {doc['_id']}, Question: {doc.get('question', 'No question')}")
            
except Exception as e:
    print(f"Error: {e}") 