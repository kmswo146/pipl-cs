"""
AI Assistant Function Library
Structured database interaction functions for AI assistant
"""

from .database import AssistantDB
from .function_registry import FunctionRegistry
from .function_loader import get_registry, get_functions_documentation, execute_function

# Initialize components
assistant_db = AssistantDB()

# Export main interface
__all__ = ['assistant_db', 'get_registry', 'get_functions_documentation', 'execute_function']