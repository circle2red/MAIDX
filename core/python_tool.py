import ast
import os
import re
import subprocess
import tempfile

tool_desc = {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Use this to perform calculations, data transformations, "
                       "or date/time conversions. The code should print() the result. "
                       "The time limit of code running is 1s, "
                       "and no input is accepted (you need to enclose the data inside your code). "
                       "Run with minimal code, avoid unnecessary comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Must use print() to output results",
                }
            },
            "required": ["code"]
        },
    }
}

def run_python(code: str) -> str:
    """
    Run the given string as Python code in a separate process with a 1-second time limit.
    No input is accepted (you need to enclose the test inputs inside your code).
    Disallows imports of certain "dangerous" modules for basic safeguarding.
    The temporary file path in error outputs is masked to "tmp.py" for repeatability.
    You will be provided with the output or any errors occurred to help you further debug.
    """

    SAFE_MODULES = {
        "datetime", "math", "json", "re", "decimal", "copy"
    }

    FORBIDDEN_NAMES = {
        'eval', 'exec', 'compile', 'open', 'input', 'getattr', 'help',
        'globals', 'locals', 'vars', 'dir', '__', 'breakpoint', '@',
    }

    def has_dangerous_imports(code: str, safe_modules: set) -> bool:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in safe_modules:
                            return True
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in safe_modules:
                        return True
                elif isinstance(node, ast.Call):
                    # Check for __import__ calls
                    if (isinstance(node.func, ast.Name) and node.func.id == "__import__" and
                            node.args and isinstance(node.args[0], ast.Str) and
                            node.args[0].s.split('.')[0] not in safe_modules):
                        return True
        except SyntaxError:
            # If code has syntax errors, parsing fails; we allow it to proceed
            # (it will fail at runtime anyway)
            pass
        return False

    if has_dangerous_imports(code, SAFE_MODULES):
        return "Error: Restricted module import detected. Dangerous modules like 'os', 'sys', 'subprocess', etc., are not allowed."
    for f in FORBIDDEN_NAMES:
        if f in code:
            return f"Error: Dangerous operation [{f}] Detected.."
    # Create a temporary file to store the Python code
    # We use delete=False then explicitly delete in finally
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py", encoding='gbk')
    # Do not use utf-8, else this would do: print(_＿name_＿)
    try:
        temp_file.write(code)
        temp_file_path = temp_file.name
    finally:
        temp_file.close()  # Close the file handle immediately after writing

    try:
        process = subprocess.run(
            ["python", temp_file_path],
            capture_output=True,
            text=True,
            timeout=1
        )

        output = process.stdout
        error_output = process.stderr

        # Mask the temporary file path in both stdout and stderr for completeness
        if output:
            escaped_temp_path = re.escape(temp_file_path)
            output = re.sub(escaped_temp_path, "tmp.py", output)
        if error_output:
            escaped_temp_path = re.escape(temp_file_path)
            error_output = re.sub(escaped_temp_path, "tmp.py", error_output)

        # Combine outputs: stdout first, then stderr if present
        combined_output = output
        if error_output:
            combined_output += f"\nError: {error_output}"

        # If returncode is non-zero and no stderr, note the exit status
        if process.returncode != 0 and not error_output:
            combined_output += f"\nProcess exited with non-zero status: {process.returncode}"

        return combined_output.strip()

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 1 second."
    except Exception as e:
        return f"Error: An unexpected error occurred during execution setup: {e}"
    finally:
        # Ensure the temporary file is cleaned up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# Test cases
if __name__ == "__main__":
    # Test 1: Simple safe code
    result1 = run_python("print('Hello, World!')")
    print("Test 1 (Safe code):", repr(result1))
    assert result1 == "Hello, World!"

    # Test 2: Code with dangerous import (should be blocked)
    result2 = run_python("import os\nprint('This should not run')")
    print("Test 2 (Dangerous import):", repr(result2))
    assert "Restricted module import detected" in result2

    # Test 3: Code with syntax error (should fail at runtime)
    result3 = run_python("print('Hello'")
    print("Test 3 (Syntax error):", repr(result3))
    assert "Error:" in result3  # Should contain syntax error details

    # Test 4: Code that times out (infinite loop)
    result4 = run_python("while True: pass")
    print("Test 4 (Timeout):", repr(result4))
    assert "timed out" in result4

    # Test 5: Code with __import__ of dangerous module (should be blocked)
    result5 = run_python("__import__('os')")
    print("Test 5 (__import__ dangerous):", repr(result5))
    assert "Restricted module import detected" in result5

    # Test 6: Safe code with output
    result6 = run_python("x = 5\nprint(x * 2)")
    print("Test 6 (Safe computation):", repr(result6))
    assert result6 == "10"

    # Test 7: Code with from import (dangerous, should be blocked)
    result7 = run_python("from os import system\nprint('Blocked')")
    print("Test 7 (From import dangerous):", repr(result7))
    assert "Restricted module import detected" in result7

    # Test 8: Code with from import (safe)
    result8 = run_python("""
import datetime
print(datetime.datetime.now())
    """)
    print("Test 8: Code with from import (safe)", repr(result8))

    print(run_python("""
#coding=utf-8
print(_＿name_＿)
""")
          )
    print("All tests passed!")
