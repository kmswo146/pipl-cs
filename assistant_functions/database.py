"""
Database Connection Module for AI Assistant
Provides standardized database access with connection management
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from pymongo import MongoClient
from datetime import datetime, timezone


class AssistantDB:
    """Database interface for AI assistant functions"""
    
    def __init__(self):
        # Production database connection (for campaigns, email accounts, etc.)
        self.app_client = MongoClient(config.APP_DB_URI)
        self.app_db = self.app_client.get_default_database()
        
        # CS bot database connection (for conversations, settings, etc.)
        self.dashboard_client = MongoClient(config.DASHBOARD_DB_URI)
        self.dashboard_db = self.dashboard_client.get_default_database()
        
        # Default to production database for assistant queries
        self.db = self.app_db
        
        # CS bot collections (from dashboard DB)
        self.intercom_conversations = self.dashboard_db.intercom_conversations
        self.qa_entries = self.dashboard_db.qa_entries
        self.settings = self.dashboard_db.settings
    
    def utc_now(self):
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc)
    
    def get_collection(self, collection_name, use_dashboard_db=False):
        """Get a database collection by name"""
        if use_dashboard_db:
            return self.dashboard_db[collection_name]
        else:
            return self.app_db[collection_name]
    
    def execute_query(self, collection_name, operation, *args, use_dashboard_db=False, **kwargs):
        """Execute a database operation with error handling"""
        try:
            collection = self.get_collection(collection_name, use_dashboard_db)
            
            # Execute the operation - READ-ONLY for safety
            if operation == 'find':
                return list(collection.find(*args, **kwargs))
            elif operation == 'find_one':
                return collection.find_one(*args, **kwargs)
            # elif operation == 'insert_one':
            #     return collection.insert_one(*args, **kwargs)
            # elif operation == 'update_one':
            #     return collection.update_one(*args, **kwargs)
            # elif operation == 'delete_one':
            #     return collection.delete_one(*args, **kwargs)
            elif operation == 'aggregate':
                return list(collection.aggregate(*args, **kwargs))
            elif operation == 'count_documents':
                return collection.count_documents(*args, **kwargs)
            else:
                raise ValueError(f"Unsupported operation: {operation} - Only read operations allowed")
                
        except Exception as e:
            print(f"Database operation error: {e}")
            return None