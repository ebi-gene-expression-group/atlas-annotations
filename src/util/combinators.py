"""
Utility functions for combining Either-like results.
This is a simple implementation of combining results with error handling.
"""
from typing import List, Tuple, Union, Any, Callable, Iterable


def do_all(f: Callable, inputs: List[Any]) -> Union[Tuple[str, None], Tuple[None, Any]]:
    """
    Apply function f to all inputs, collecting errors.
    
    Args:
        f: Function that returns (error, result) tuple
        inputs: List of inputs to process
    
    Returns:
        (None, None) on success, (error_message, None) on failure
    """
    errors = []
    for inp in inputs:
        error, _ = f(inp)
        if error:
            errors.append((inp, error))
    
    if not errors:
        return (None, None)
    else:
        error_msg = f"{len(errors)} errors:\n" + "\n".join(str(e) for e in errors)
        return (error_msg, None)


def combine(data: Iterable[Tuple[Any, Any]]) -> Tuple[Any, Any]:
    """
    Combine a list of (error, result) tuples.
    
    Returns:
        (None, [results]) if all succeeded
        ([errors], None) if any failed
    """
    lefts = []
    rights = []
    
    for item in data:
        error, result = item
        if error is not None:
            lefts.append(error)
        else:
            rights.append(result)
    
    if not lefts:
        return (None, rights)
    else:
        return (lefts, None)


def combine_any(data: Iterable[Tuple[Any, Any]]) -> Tuple[Any, Any]:
    """
    Combine a list of (error, result) tuples, accepting any successes.
    
    Returns:
        (None, [results]) if at least one succeeded
        ([errors], None) if all failed
    """
    lefts = []
    rights = []
    
    for item in data:
        error, result = item
        if error is not None:
            lefts.append(error)
        else:
            rights.append(result)
    
    if rights:
        return (None, rights)
    else:
        return (lefts, None)
