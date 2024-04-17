# metagpt/tools/libs/calculate_factorial.py
import math
from metagpt.tools.tool_registry import register_tool

# Register tool with the decorator
@register_tool()
def calculate_factorial(n):
    """
    Calculate the factorial of a non-negative integer.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    return math.factorial(n)