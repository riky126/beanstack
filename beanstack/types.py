from collections.abc import Mapping

class ActionTypes(object):
    INIT = '@@pyredux/INIT'

class ImmutableDict:
    """
    A simple immutable dictionary implementation.
    """
    def __init__(self, data=None):
        self._data = {}
        if data:
            for key, value in data.items():
                if isinstance(value, Mapping):
                    self._data[key] = ImmutableDict(value)
                elif isinstance(value, list):
                    self._data[key] = ImmutableList(value)
                else:
                    self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def to_dict(self):
        """Convert the ImmutableDict to a regular dictionary."""
        result = {}
        for key, value in self._data.items():
            if isinstance(value, (ImmutableDict, ImmutableList)):
                result[key] = value.to_dict() if isinstance(value, ImmutableDict) else value.to_list()
            else:
                result[key] = value
        return result

    def __repr__(self):
        """Provide a string representation of the ImmutableDict."""
        return f"ImmutableDict({repr(self._data)})"

    def __eq__(self, other):
        """Check equality with another ImmutableDict."""
        if isinstance(other, ImmutableDict):
            return self._data == other._data
        return False

    def __hash__(self):
        """Compute a hash value for the ImmutableDict."""
        return hash(frozenset(self._data.items()))


class ImmutableList:
    """
    A simple immutable list implementation.
    """
    def __init__(self, data=None):
        self._data = []
        if data:
            for item in data:
                if isinstance(item, Mapping):
                    self._data.append(ImmutableDict(item))
                elif isinstance(item, list):
                    self._data.append(ImmutableList(item))
                else:
                    self._data.append(item)

    def __getitem__(self, index):
        return self._data[index]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def to_list(self):
        """Convert the ImmutableList to a regular list."""
        result = []
        for item in self._data:
            if isinstance(item, (ImmutableDict, ImmutableList)):
                result.append(item.to_dict() if isinstance(item, ImmutableDict) else item.to_list())
            else:
                result.append(item)
        return result

    def __repr__(self):
        """Provide a string representation of the ImmutableList."""
        return f"ImmutableList({repr(self._data)})"

    def __eq__(self, other):
        """Check equality with another ImmutableList."""
        if isinstance(other, ImmutableList):
            return self._data == other._data
        return False

    def __hash__(self):
        """Compute a hash value for the ImmutableList."""
        return hash(tuple(self._data))
