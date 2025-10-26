"""
Tools for LLM function calling
"""
import sys
from io import StringIO
from typing import Dict, Any
import ast


def execute_python_tool(code: str) -> Dict[str, Any]:
    """
    Execute Python code in a restricted environment

    Args:
        code: Python code to execute

    Returns:
        Dictionary with 'success', 'output', and optionally 'error'
    """
    # Restricted globals - only safe built-ins and common modules
    safe_builtins = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'float': float,
        'int': int,
        'len': len,
        'list': list,
        'max': max,
        'min': min,
        'print': print,
        'range': range,
        'round': round,
        'set': set,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'type': type,
        'enumerate': enumerate,
        'zip': zip,
        'sorted': sorted,
        'reversed': reversed,
    }

    # Safe modules that can be imported
    safe_modules = {
        'datetime': __import__('datetime'),
        'json': __import__('json'),
        'math': __import__('math'),
        're': __import__('re'),
    }

    # Custom __import__ function that only allows safe modules
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in safe_modules:
            return safe_modules[name]
        raise ImportError(f"Import of '{name}' is not allowed. Only datetime, json, math, re are permitted.")

    # Add __import__ to safe builtins
    safe_builtins_with_import = {
        **safe_builtins,
        '__import__': safe_import,
    }

    # Create restricted globals
    restricted_globals = {
        '__builtins__': safe_builtins_with_import,
        **safe_modules
    }

    # Validate code - check for dangerous operations
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Block imports (except allowed ones)
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in safe_modules:
                            return {
                                'success': False,
                                'error': f"Import of '{alias.name}' is not allowed. Only datetime, json, math, re are permitted."
                            }
                elif isinstance(node, ast.ImportFrom):
                    if node.module not in safe_modules:
                        return {
                            'success': False,
                            'error': f"Import from '{node.module}' is not allowed. Only datetime, json, math, re are permitted."
                        }

            # Block file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'exec', 'eval', 'compile']:
                        return {
                            'success': False,
                            'error': f"Function '{node.func.id}' is not allowed for security reasons."
                        }

    except SyntaxError as e:
        return {
            'success': False,
            'error': f"Syntax error in code: {str(e)}"
        }

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    try:
        # Execute the code
        exec(code, restricted_globals, {})

        # Get the output
        output = captured_output.getvalue()

        return {
            'success': True,
            'output': output.strip()
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"{type(e).__name__}: {str(e)}"
        }

    finally:
        # Restore stdout
        sys.stdout = old_stdout


def test_python_tool():
    """Test the Python execution tool"""
    # Test 1: Simple calculation
    result = execute_python_tool("print(2 + 2)")
    print("Test 1 - Simple calculation:", result)

    # Test 2: DateTime conversion
    result = execute_python_tool("""
import datetime
dt = datetime.datetime(2025, 1, 1)
timestamp = int(dt.timestamp())
print(timestamp)
""")
    print("Test 2 - DateTime conversion:", result)

    # Test 3: Blocked operation (file access)
    result = execute_python_tool("open('test.txt', 'w')")
    print("Test 3 - Blocked file access:", result)

    # Test 4: Blocked import
    result = execute_python_tool("import os")
    print("Test 4 - Blocked import:", result)

    # Test 5: Blocked import
    result = execute_python_tool("from os import getcwd\nprint(getcwd())\n")
    print("Test 5", result)

if __name__ == "__main__":
    test_python_tool()
