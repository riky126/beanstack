from typing import Any, Optional, Protocol
import json
import os

from .runtime import is_server_side

if is_server_side:
    session_storage = None
    local_storage = None
else:
    from js import Object, localStorage, sessionStorage


class StorageEngine(Protocol):
    """Protocol defining the interface for storage engines."""
    def save(self, key: str, data: Any) -> None: ...
    def load(self, key: str) -> Optional[Any]: ...
    def remove(self, key: str, attr_key: str) -> None: ...
    def clear(self, key: str) -> None: ...

class FileStorage:
    """File-based storage engine implementation."""
    def __init__(self, directory: str = ".store"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def save(self, key: str, data: Any) -> None:
        path = os.path.join(self.directory, f"{key}.json")
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def load(self, key: str) -> Optional[Any]:
        path = os.path.join(self.directory, f"{key}.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        
    def remove(self, key: str, attr_key: str) -> None:
        pass
    
    def clear(self, key: str) -> None:
        path = os.path.join(self.directory, f"{key}.json")
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

class MemoryStorage:
    """In-memory storage engine implementation."""
    def __init__(self):
        self._storage = {}
    
    def save(self, key: str, data: Any) -> None:
        self._storage[key] = json.dumps(data)
    
    def load(self, key: str) -> Optional[Any]:
        
        if key in self._storage:
            print(f"load: {json.loads(self._storage[key])}")
            return json.loads(self._storage[key])
        return None
    
    def remove(self, key: str, attr_key: str) -> None:
        pass
    
    def clear(self, key: str) -> None:
        self._storage.pop(key, None)


class BrowserStorage:
    """
    Provides dictionary-like interface to browser storage objects.

    Attributes:
        _storage: The browser storage object (e.g., localStorage, sessionStorage).
        description (str): Description of the storage instance.

    """

    class NoDefault:
        """Placeholder class for default values when no default is provided."""

        pass

    def __init__(self, storage_target, description):
        """
        Initializes the BrowserStorage instance.

        Args:
            _storage: The browser storage object.
            description (str): Description of the storage instance.
        """
        self._storage = storage_target
        self.description = description

    def save(self, key: str, data: Any) -> None:
        
        self._storage.setItem(key, json.dumps(data))
    
    def load(self, key: str) -> Optional[Any]:
        value_json = self._storage.getItem(key)

        if value_json:
            data = json.loads(value_json)
            print(f"load: {data}")
            if data is not None:
                return data
            
        return None   
    
    def remove(self, key: str, attr_key: str) -> None:
        data = self.load(key)

        if data and attr_key in data:
            del data[attr_key]
            self.save(key, data)

    def clear(self, key: str):
        """
        Clears all items from the storage.
        """
        self._storage.removeItem(key)


session_storage = BrowserStorage(sessionStorage, "session_storage")
local_storage = BrowserStorage(localStorage, "local_storage")