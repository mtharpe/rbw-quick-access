"""
A global, cross-platform(ish) handler for tons of things.
"""

from platform import mac_ver

from PyQt6.QtCore import QObject, pyqtSignal

IS_MAC = bool(mac_ver()[0])


class PlatformHandler(QObject):
    """A common Platform Handler superclass to be used for specific niche oddities (looking at you macOS)"""

    on_show_signal = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def on_show(self):
        """Used to allow platform-specific callbacks on the show event"""

    def on_hide(self):
        """Used to allow platform-specific callbacks on the hide event"""


def get_platform_handler(parent: QObject) -> PlatformHandler:
    if IS_MAC:
        from plat.macos import MacOsPlatformHandler

        return MacOsPlatformHandler(parent)
    return PlatformHandler()
