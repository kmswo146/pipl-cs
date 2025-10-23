"""
Function Loader
Loads and registers all available functions for the AI assistant
"""

from .function_registry import FunctionRegistry
# Import your function sections here when you create them
from .sections.check_user_plan import register_user_plan_functions
from .sections.campaigns import register_campaign_functions


def load_all_functions():
    """Load all available functions into the registry"""
    registry = FunctionRegistry()
    
    # Register all function sections here when you create them
    register_user_plan_functions(registry)
    register_campaign_functions(registry)
    
    return registry


def get_functions_documentation():
    """Get comprehensive documentation for AI consumption"""
    registry = load_all_functions()
    return registry.get_documentation(for_ai=True)


def execute_function(function_name, **kwargs):
    """Execute a function by name with parameters"""
    registry = load_all_functions()
    return registry.execute_function(function_name, **kwargs)


# For easy access
_registry = None

def get_registry():
    """Get the function registry (singleton pattern)"""
    global _registry
    if _registry is None:
        _registry = load_all_functions()
    return _registry