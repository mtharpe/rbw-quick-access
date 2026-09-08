from collections.abc import Callable


class Hotkey:
    """A generic superclass defining common function definitions for each hotkey variant"""

    def __init__(self):
        raise NotImplementedError()

    def register_hotkey(self, callback: Callable):
        raise NotImplementedError()

    def unregister_hotkey(self):
        raise NotImplementedError()
