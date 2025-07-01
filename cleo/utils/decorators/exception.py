import sys
import functools
from typing import Callable, Any
import os
import rich

def disable_traceback(func: Callable) -> Callable:
    """
    Decorator that disables tracebacks and rich formatting for a specific Typer command.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            sys.tracebacklimit = 0
            os.environ['_TYPER_STANDARD_TRACEBACK'] = '1'
            
            # Create a plain console without color/markup
            rich.console._console = rich.console.Console(
                color_system=None, 
                highlight=False,
                markup=False,
                emoji=False
            )
        
            # Execute the original function
            return func(*args, **kwargs)
            
        except Exception as e:
            # Print only the error message without traceback or rich formatting
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)    
    return wrapper