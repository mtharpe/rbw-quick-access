"""
A global, cross-platform(ish) keybind handler
"""

from PyQt6.QtCore import QObject, pyqtBoundSignal

from macos import IS_MAC

class KeybindListener

def get_hotkey_listener(parent: QObject) -> QObject | None:
    if IS_MAC:
        from macos import MacOSHotkeyListener

        return MacOSHotkeyListener(parent)
    return None
