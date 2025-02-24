from collections.abc import Mapping
from typing import Dict, Any

    
def combine_state(initial_state: Dict[Any, Any], stored_state: Dict[Any, Any]) -> Dict[Any, Any]:

    """
    Match stored state to state of store, merging nested dictionaries.
    
    Args:
        initial_state: The initial state dictionary
        stored_state: The stored state dictionary to merge
    Returns:
        Merged state dictionary
    """
    # Create a shallow copy of initial_state
    merged_state = dict(initial_state)
    
    for key, stored_value in stored_state.items():
        if key not in merged_state:
            merged_state[key] = stored_value
        else:
            initial_value = merged_state[key]
            if isinstance(initial_value, Mapping) and isinstance(stored_value, Mapping):
                merged_state[key] = combine_state(initial_value, stored_value)
            elif initial_value != stored_value:
                merged_state[key] = stored_value
    
    return merged_state