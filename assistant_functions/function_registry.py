"""
Function Registry for AI Assistant
Manages available functions organized by sections with documentation
"""

import json
import os
from typing import Dict, List, Any, Optional


class FunctionDefinition:
    """Represents a function that the AI assistant can call"""
    
    def __init__(self, name: str, description: str, section: str, 
                 inputs: Dict[str, Any], outputs: Dict[str, Any], 
                 function_callable, examples: List[str] = None):
        self.name = name
        self.description = description
        self.section = section
        self.inputs = inputs  # Parameter definitions
        self.outputs = outputs  # Return value definitions
        self.function_callable = function_callable
        self.examples = examples or []
    
    def to_dict(self):
        """Convert to dictionary for AI consumption"""
        return {
            "name": self.name,
            "description": self.description,
            "section": self.section,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "examples": self.examples
        }


class FunctionRegistry:
    """Registry of all functions available to the AI assistant"""
    
    def __init__(self):
        self.functions: Dict[str, FunctionDefinition] = {}
        self.sections: Dict[str, str] = {}  # section_name -> description
        self.context_info: Dict[str, str] = {}  # section_name -> context text
        
        # Load any existing function definitions
        self._load_sections()
    
    def register_function(self, function_def: FunctionDefinition):
        """Register a new function"""
        self.functions[function_def.name] = function_def
    
    def register_section(self, section_name: str, description: str, context_file: str = None):
        """Register a section with optional context file"""
        self.sections[section_name] = description
        
        if context_file:
            context_path = os.path.join(os.path.dirname(__file__), 'context', f'{context_file}.txt')
            if os.path.exists(context_path):
                with open(context_path, 'r') as f:
                    self.context_info[section_name] = f.read()
    
    def get_functions_by_section(self, section: str) -> List[FunctionDefinition]:
        """Get all functions in a specific section"""
        return [func for func in self.functions.values() if func.section == section]
    
    def get_function(self, name: str) -> Optional[FunctionDefinition]:
        """Get a specific function by name"""
        return self.functions.get(name)
    
    def execute_function(self, name: str, **kwargs):
        """Execute a function by name with parameters"""
        func_def = self.get_function(name)
        if not func_def:
            raise ValueError(f"Function '{name}' not found")
        
        try:
            return func_def.function_callable(**kwargs)
        except Exception as e:
            print(f"Error executing function '{name}': {e}")
            return {"error": str(e)}
    
    def get_documentation(self, for_ai: bool = True) -> Dict[str, Any]:
        """Get complete documentation for AI or human consumption"""
        if for_ai:
            # Format optimized for AI understanding
            return {
                "sections": {
                    section: {
                        "description": desc,
                        "context": self.context_info.get(section, ""),
                        "functions": [func.to_dict() for func in self.get_functions_by_section(section)]
                    }
                    for section, desc in self.sections.items()
                }
            }
        else:
            # Human-readable format
            return {
                "total_functions": len(self.functions),
                "sections": list(self.sections.keys()),
                "functions": {name: func.to_dict() for name, func in self.functions.items()}
            }
    
    def _load_sections(self):
        """Load predefined sections"""
        # This will be called by individual section modules
        pass