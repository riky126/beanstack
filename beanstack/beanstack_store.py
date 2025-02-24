import threading
from copy import deepcopy
from typing import Callable, Dict, Any, Optional, List
from collections import deque
from datetime import datetime

from .types import ImmutableDict
from .storage import StorageEngine
from .utils import combine_state


class TimeTravel:
    """Manages state history for time travel debugging."""
    
    def __init__(self, max_history: int = 50):
        self.history = deque(maxlen=max_history)
        self.current_index = -1
        self.lock = threading.Lock()
        
    def push_state(self, state: Dict, action: Dict):
        """Add new state to history."""
        with self.lock:
            if self.current_index < len(self.history) - 1:
                self.history = deque(list(self.history)[:self.current_index + 1], maxlen=self.history.maxlen)
            
            self.history.append({
                'state': deepcopy(state),
                'action': deepcopy(action),
                'timestamp': datetime.now().isoformat()
            })
            self.current_index = len(self.history) - 1
            
    def get_state(self, index: int) -> Optional[Dict]:
        """Get state at specific index."""
        with self.lock:
            if 0 <= index < len(self.history):
                return deepcopy(self.history[index]['state'])
        return None
        
    def get_current_state(self) -> Optional[Dict]:
        """Get current state in time travel history."""
        with self.lock:
            if self.current_index >= 0:
                return deepcopy(self.history[self.current_index]['state'])
        return None
    
    def get_history(self) -> List[Dict]:
        """Get list of all actions and timestamps."""
        with self.lock:
            return [
                {
                    'index': i,
                    'action': item['action'],
                    'timestamp': item['timestamp'],
                    'active': i == self.current_index
                }
                for i, item in enumerate(self.history)
            ]

class beanstackStore:
    """
    A Python implementation of a Redux-like store with thread-safe state management,
    time travel debugging, and state persistence capabilities.
    """

    def __init__(
        self, 
        reducer: Callable, 
        initial_state: Optional[Dict[str, Any]] = None,
        storage_engine: Optional[StorageEngine] = None,
        storage_key: str = "beanstack_state",
        persist_keys: Optional[List[str]] = None
    ):
        if not callable(reducer):
            typeof = type(reducer)
            raise Exception(f"Expected the root reducer to be a function. Instead, received: {typeof.__name__}")

        self._reducer = reducer
        self._storage = storage_engine
        self._storage_key = storage_key
        self._persist_keys = persist_keys
        self.devtools = None
        
        # Try to rehydrate state from storage
        rehydrated_state = self._rehydrate_state()
        base_state = initial_state or {}
        merge_state = combine_state(base_state, rehydrated_state) if rehydrated_state else base_state

        self._state = ImmutableDict(merge_state)
        self._subscribers = []
        self._lock = threading.RLock()
        self._time_travel = TimeTravel()
        self._debug_mode = False

    
    def _rehydrate_state(self) -> Optional[Dict]:
        """Attempt to load state from storage."""
        if not self._storage:
            return None
            
        stored_state = self._storage.load(self._storage_key)
        if not stored_state:
            return None
            
        if self._persist_keys:
            # Only rehydrate specified keys
            return {
                key: stored_state[key]
                for key in self._persist_keys
                if key in stored_state
            }
        
        return stored_state

    def _persist_state(self) -> None:
        """Save current state to storage."""
        if self._storage is None:
            return
        
        state_to_persist = self._state.to_dict()
        if self._persist_keys:
            # Only persist specified keys
            state_to_persist = {
                key: state_to_persist[key]
                for key in self._persist_keys
                if key in state_to_persist
            }
            
        self._storage.save(self._storage_key, state_to_persist)

    def get_state(self, slice_key=None) -> Dict[str, Any]:
        """Return current state, considering time travel if enabled."""
        with self._lock:
            if self._debug_mode:
                state = self._time_travel.get_current_state()
                if state is not None:
                    if slice_key:
                        return state.get(slice_key)
                    return deepcopy(state)
            
            if slice_key:
                return self._state.get(slice_key)
            return deepcopy(self._state.to_dict())

    def _base_dispatch(self, action: Dict[str, Any]) -> None:
        """Base dispatch function that updates state and notifies subscribers."""
        if not isinstance(action, dict) or 'type' not in action:
            raise ValueError("Actions must be dictionaries with a 'type' key.")

        with self._lock:
            new_state = self._reducer(self._state.to_dict(), action)
            self._state = ImmutableDict(new_state)
            
            if self._debug_mode:
                self._time_travel.push_state(new_state, action)
            
            # Persist state after update
            self._persist_state()
                
            self._notify_subscribers()
            return action

    def dispatch(self, action: Dict[str, Any]) -> Any:
        """Dispatch an action to modify the state."""
        return self._base_dispatch(action)

    def subscribe(self, listener: Callable) -> Callable:
        """Subscribe to state changes."""
        with self._lock:
            self._subscribers.append(listener)
        return lambda: self._unsubscribe(listener)

    def _unsubscribe(self, listener: Callable) -> None:
        """Unsubscribe a listener from state changes."""
        with self._lock:
            if listener in self._subscribers:
                self._subscribers.remove(listener)

    def _notify_subscribers(self) -> None:
        """Notify all subscribers of state changes."""
        with self._lock:
            for subscriber in list(self._subscribers):
                if hasattr(subscriber, "redraw"):
                    subscriber.redraw()
                elif callable(subscriber):
                    subscriber()

    # Time Travel Debugging Methods
    def enable_debug(self):
        """Enable time travel debugging."""
        with self._lock:
            if not self._debug_mode:
                self._debug_mode = True
                self._time_travel.push_state(self._state.to_dict(), {"type": "@@INIT"})

    def disable_debug(self):
        """Disable time travel debugging."""
        with self._lock:
            if self._debug_mode:
                self._debug_mode = False
                latest_state = self._time_travel.get_state(len(self._time_travel.history) - 1)
                if latest_state:
                    self._state = ImmutableDict(latest_state)
                    self._persist_state()

    def time_travel_to(self, index: int):
        """Jump to a specific point in history."""
        with self._lock:
            if not self._debug_mode:
                raise RuntimeError("Time travel is only available in debug mode")
            
            state = self._time_travel.get_state(index)
            if state is not None:
                self._time_travel.current_index = index
                self._notify_subscribers()

    def get_history(self) -> List[Dict]:
        """Get the action history for debugging."""
        if not self._debug_mode:
            raise RuntimeError("History is only available in debug mode")
        return self._time_travel.get_history()
    
    # Persistence Methods
    def remove_persisted_slice(self, slice_key: str) -> None:
        """Clear the persisted state from storage."""
        if self._storage:
            self._storage.remove(self._storage_key, slice_key)


    def clear_persisted_state(self) -> None:
        """Clear the persisted state from storage."""
        if self._storage:
            self._storage.clear(self._storage_key)


def combine_reducers(reducers: Dict[str, Callable]) -> Callable:
    """
    Combine multiple reducers into a single reducer function.

    Args:
        reducers: Dictionary mapping state keys to reducer functions.

    Returns:
        Callable: Combined reducer function.
    """
    registered_reducers: Dict[str, Callable] = {}
    
    for key, reducer in reducers.items():
        if not callable(reducer):
            typeof = type(reducer)
            raise Exception(f"Expected reducer to be a function. Instead, received: {typeof.__name__}")
        else:
            registered_reducers[key] = reducer

    def combined_reducer(state: Dict[str, Any] = None, action: Dict[str, Any] = None) -> Dict[str, Any]:
        if state is None:
            state = {}
        
        next_state = {
            key: reducer(state.get(key), action)
            for key, reducer in registered_reducers.items()
        }
        return ImmutableDict(next_state)
    return combined_reducer


# Store creator function
def create_store(
    reducer: Callable, 
    initial_state: Optional[Dict[str, Any]] = None,
    storage_engine: Optional[StorageEngine] = None,
    storage_key: str = "beanstack_state",
    persist_keys: Optional[List[str]] = None
):
    """Create a new store instance with optional persistence."""
    return beanstackStore(
        reducer, 
        initial_state, 
        storage_engine=storage_engine,
        storage_key=storage_key,
        persist_keys=persist_keys
    )

