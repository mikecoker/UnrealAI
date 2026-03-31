"""Python Script Execution tools: execute Python code within Unreal Engine context."""
import json
import logging
import re
from mcp_server import client

# Set up logging
logger = logging.getLogger(__name__)

def _check(result: dict) -> dict:
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Unknown error from UE5 plugin"))
    return result


def _execute_python_script(script_content: str, safe_mode: bool = True) -> str:
    """Execute Python script within Unreal Engine context with safety checks."""
    
    # Safety checks for potentially destructive operations
    if safe_mode:
        dangerous_patterns = [
            r"import\s+os",
            r"import\s+subprocess",
            r"exec\(",
            r"eval\(",
            r"os\.",
            r"sys\.",
            r"__import__",
            r"open\(",
            r"write\(",
            r"delete\(",
            r"remove\(",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                raise ValueError(f"Potentially unsafe operation detected: {pattern}")
    
    try:
        # Call the UE5 plugin endpoint to execute Python code
        r = _check(client.post("/python/execute", {
            "script": script_content,
            "safe_mode": safe_mode
        }))
        
        result = r.get("result", "")
        if result:
            return f"Python execution result:\n{result}"
        else:
            return "Python script executed successfully (no output)"
            
    except Exception as e:
        logger.error(f"Error executing Python script: {str(e)}")
        raise RuntimeError(f"Failed to execute Python script: {str(e)}")


def _execute_python_file(file_path: str, safe_mode: bool = True) -> str:
    """Execute a Python file within Unreal Engine context."""
    
    # Safety checks for potentially destructive operations
    if safe_mode:
        dangerous_patterns = [
            r"import\s+os",
            r"import\s+subprocess",
            r"exec\(",
            r"eval\(",
            r"os\.",
            r"sys\.",
            r"__import__",
            r"open\(",
            r"write\(",
            r"delete\(",
            r"remove\(",
        ]
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    raise ValueError(f"Potentially unsafe operation detected in {file_path}: {pattern}")
        except Exception as e:
            raise RuntimeError(f"Failed to read file or check safety: {str(e)}")
    
    try:
        # Call the UE5 plugin endpoint to execute Python script from file
        r = _check(client.post("/python/execute_file", {
            "file_path": file_path,
            "safe_mode": safe_mode
        }))
        
        result = r.get("result", "")
        if result:
            return f"Python file execution result:\n{result}"
        else:
            return "Python script executed successfully (no output)"
            
    except Exception as e:
        logger.error(f"Error executing Python file: {str(e)}")
        raise RuntimeError(f"Failed to execute Python file: {str(e)}")


def register(mcp):
    @mcp.tool()
    def execute_python_script(script_content: str, safe_mode: bool = True) -> str:
        """Execute a Python script within Unreal Engine context with safety checks.
        
        Args:
            script_content (str): The Python code to execute
            safe_mode (bool): Enable safety checks for potentially destructive operations
            
        Returns:
            str: Execution result or error message
        """
        return _execute_python_script(script_content, safe_mode)

    @mcp.tool()
    def execute_python_file(file_path: str, safe_mode: bool = True) -> str:
        """Execute a Python file within Unreal Engine context with safety checks.
        
        Args:
            file_path (str): Path to the Python file to execute
            safe_mode (bool): Enable safety checks for potentially destructive operations
            
        Returns:
            str: Execution result or error message
        """
        return _execute_python_file(file_path, safe_mode)