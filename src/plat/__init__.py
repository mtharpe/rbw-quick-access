"""
A global, cross-platform(ish) handler for tons of things.
"""

from platform import mac_ver

from PyQt6.QtCore import QObject, pyqtSignal

IS_MAC = bool(mac_ver()[0])


class GlobalShowListener(QObject):
    """A relatively barebone impl just for the signal to be unified"""

    signal = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def on_show(self):
        """Used to allow platform-specific callbacks"""

def get_global_show_listener(parent: QObject) -> GlobalShowListener:
    if IS_MAC:
        from plat.macos import MacOSGlobalShowListener

        return MacOSGlobalShowListener(parent)
    return GlobalShowListener()
