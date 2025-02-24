# Create middleware support
import time
import traceback
import asyncio
from functools import reduce, wraps
from typing import Callable, Any, Dict, Optional

from .types import ActionTypes

class StoreApi:
    def __init__(self, dispatch: Optional[Callable[[Any], Any]] = None, get_state: Optional[Callable[[], Any]] = None):
        self.dispatch = dispatch
        self.get_state = get_state


def middleware(middleware_func):
    """
    Decorator to add a type check to all middleware so they skip non-dictionary actions (e.g., thunks).
    """
    @wraps(middleware_func)
    def wrapper(store):
        base_middleware = middleware_func(store)

        def enhanced_dispatch(next_dispatch):
            base_dispatch = base_middleware(next_dispatch)

            def dispatch(action):
                # Skip processing if action is a function (thunk)
                if not isinstance(action, dict):
                    return next_dispatch(action)
                return base_dispatch(action)
            return dispatch
        return enhanced_dispatch
    return wrapper


def apply_middleware(*middlewares):
    """
    Apply middleware to the store.

    Args:
        *middlewares: Variable number of middleware functions.

    Returns:
        A store enhancer function that takes a store creator and returns an enhanced store.
    """
    def store_enhancer(create_store_func):
        def enhanced_create_store(reducer, initial_state=None, **store_args):
            store = create_store_func(reducer, initial_state, **store_args)
            dispatch = store.dispatch
            
            # Middleware API shared with all middleware
            store_api = StoreApi(
                get_state=store.get_state,
                dispatch=lambda action: dispatch(action)  # Will refer to enhanced dispatch after composition
            )
            
            # Compose middleware chain
            chain = [middleware(store_api) for middleware in reversed(middlewares)]
            dispatch = reduce(lambda acc, curr: curr(acc), chain, store.dispatch)

            # Final enhanced dispatch assigned back to the store
            store.dispatch = dispatch

            # Dispatch @@INIT after middleware setup
            store.dispatch({"type": ActionTypes.INIT})
            return store
        return enhanced_create_store
    return store_enhancer


@middleware
def logger_middleware(store):
    """
    Middleware that logs actions and state changes.
    """
    def middleware(next_dispatch):
        def dispatch(action):
        
            action_type = action.get('type', 'UNKNOWN')
            payload = f" Payload: {action.get('payload')}" if 'payload' in action else ''

            print(f"\n🔵 Action: {action_type}{payload}")
            print(f"Previous State: {store.get_state()}")
            
            start_time = time.time()
            result = next_dispatch(action)
            duration = (time.time() - start_time) * 1000

            print(f"Next State: {store.get_state()}")
            print(f"Time: {duration:.2f}ms")
            return result
        return dispatch
    return middleware

def thunk_middleware(store):
    """
    Middleware that enables dispatching async actions (thunks).
    """
    def middleware(next_dispatch):
        def dispatch(action):
            if callable(action):
                return action(store.dispatch, store.get_state)
            return next_dispatch(action)
        return dispatch
    return middleware

def async_thunk_middleware(store):
    """
    Middleware that enables dispatching async coroutine actions (async thunks).
    """
    def middleware(next_dispatch):
        async def dispatch(action):
            if asyncio.iscoroutinefunction(action):
                return await action(store.dispatch, store.get_state)
            return next_dispatch(action)
        return dispatch
    return middleware

@middleware
def error_middleware(store):
    """
    Middleware that handles errors during dispatch.
    """
    def middleware(next_dispatch):
        def dispatch(action):
            try:
                return next_dispatch(action)
            except Exception as e:
                action_type = action.get('type', 'UNKNOWN')
                print(f"\n🔴 Error processing action {action_type}:")
                print(f"Error: {str(e)}")
                print("Stack trace:")
                print(traceback.format_exc())

                # Prevent infinite error dispatch loops
                if action.get('type') != 'ERROR':
                    store.dispatch({
                        'type': 'ERROR',
                        'payload': {
                            'action': action,
                            'error': str(e)
                        }
                    })
                raise  # Re-raise for further upstream handling
        return dispatch
    return middleware

def debounce_middleware(delay_ms=1000):
    """
    Middleware that debounces actions of the same type.
    """
    last_action_time = {}
    
    @middleware
    def middleware(store):
        def wrapper(next_dispatch):
            def dispatch(action):
                action_type = action.get('type', 'UNKNOWN')
                current_time = time.monotonic() * 1000

                if action_type in last_action_time:
                    time_diff = current_time - last_action_time[action_type]
                    if time_diff < delay_ms:
                        print(f"\n⏳ Debouncing action {action_type}")
                        return None

                last_action_time[action_type] = current_time
                return next_dispatch(action)
            return dispatch
        return wrapper
    return middleware