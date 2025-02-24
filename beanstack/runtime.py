import sys

PLATFORM_PYODIDE = "pyodide"
PLATFORM_MICROPYTHON = "micropython"
PLATFORM_CPYTHON = "cpython"


def _detect_platform():
    if sys.platform == "emscripten":
        return PLATFORM_PYODIDE
    elif sys.platform == "webassembly" and sys.implementation.name == "micropython":
        return PLATFORM_MICROPYTHON
    elif sys.implementation.name == "cpython":
        return PLATFORM_CPYTHON


platform = _detect_platform()
is_server_side = platform not in (PLATFORM_PYODIDE, PLATFORM_MICROPYTHON)