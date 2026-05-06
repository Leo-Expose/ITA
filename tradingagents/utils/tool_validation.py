"""Tool validation and error handling utilities."""

import json
import re
from datetime import datetime
from typing import Any, Dict


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_valid_date(date_value: str) -> bool:
    if not DATE_RE.match(date_value):
        return False
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _sanitize_symbol(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9\^\.]", "", value or "")
    return clean.upper()[:20]


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize tool parameters to prevent malformed function calls.
    
    Args:
        tool_name: Name of the tool being called
        parameters: Raw parameters from LLM
        
    Returns:
        Sanitized parameters dictionary
    """
    if not isinstance(parameters, dict):
        return {}
    
    sanitized = {}
    
    for key, value in parameters.items():
        # Sanitize string values
        if isinstance(value, str):
            # Remove HTML tags and special characters
            clean_value = re.sub(r'<[^>]*>', '', value)
            clean_value = re.sub(r'[^\w\s\-\.\:\,\/]', '', clean_value)
            clean_value = clean_value.strip()

            if key == "symbol":
                clean_value = _sanitize_symbol(clean_value)
                if not clean_value:
                    continue
                sanitized[key] = clean_value
                continue

            if key in {"start_date", "end_date", "curr_date"}:
                if not _is_valid_date(clean_value):
                    continue
                sanitized[key] = clean_value
                continue

            if key in {"look_back_days", "limit"}:
                try:
                    int_val = int(clean_value)
                    sanitized[key] = max(1, min(365, int_val))
                except ValueError:
                    continue
                continue

            sanitized[key] = clean_value
        else:
            sanitized[key] = value
    
    return sanitized


def safe_tool_call(tool_func, tool_name: str, **kwargs) -> Dict[str, Any]:
    """Safely execute a tool call with validation and error handling.
    
    Args:
        tool_func: Tool function to call
        tool_name: Name of the tool for validation
        **kwargs: Tool parameters
        
    Returns:
        Dictionary with success status and result or error
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters(tool_name, kwargs)
        
        # Check for required parameters
        if not validated_params:
            return {
                "success": False,
                "error": f"Invalid parameters for {tool_name}",
                "result": None
            }
        
        # Execute tool with validated parameters
        result = tool_func(**validated_params)
        
        return {
            "success": True,
            "result": result,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool {tool_name} failed: {str(e)}",
            "result": None
        }


def parse_function_call(function_call_str: str) -> Dict[str, Any]:
    """Parse and validate function call string to prevent malformed JSON.
    
    Args:
        function_call_str: Raw function call string from LLM
        
    Returns:
        Parsed function call dictionary
    """
    try:
        # Remove HTML tags and clean the string
        clean_str = re.sub(r'<[^>]*>', '', function_call_str)
        clean_str = clean_str.strip()
        
        # Try to parse as JSON
        if clean_str.startswith('{') and clean_str.endswith('}'):
            return json.loads(clean_str)
        
        # Try to extract function name and parameters
        if '(' in clean_str and ')' in clean_str:
            func_name = clean_str.split('(')[0].strip()
            params_str = clean_str.split('(')[1].split(')')[0].strip()
            
            return {
                "function": func_name,
                "parameters": params_str
            }
        
        return {}
        
    except Exception:
        return {}


def create_fallback_response(tool_name: str, error_message: str) -> str:
    """Create a standardized fallback response for tool failures.
    
    Args:
        tool_name: Name of the failed tool
        error_message: Error description
        
    Returns:
        Formatted fallback response
    """
    return f"""
    Tool {tool_name} encountered an error: {error_message}
    
    Fallback Analysis:
    - Unable to fetch real-time data due to technical issues
    - Please try again later or check data source directly
    - For Indian stocks, you can check NSE website manually
    - Consider using cached data if available
    
    Recommendation: 
    - Retry the analysis after checking network connectivity
    - Verify stock symbol is correct (e.g., RELIANCE, TCS.NS)
    - Check if market is open (9:15 AM - 3:30 PM IST)
    """
