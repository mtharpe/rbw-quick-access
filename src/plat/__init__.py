"""
A global, cross-platform(ish) handler for tons of things.
"""

from os import execv
from sys import argv, executable, platform

from PyQt6.QtCore import QObject, pyqtSignal

IS_MAC = platform == "darwin"
IS_LINUX = platform == "linux"


class PlatformHandler(QObject):
    """A common Platform Handler superclass to be used for specific niche oddities (looking at you macOS)"""

    on_show_signal = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def on_show(self):
        """Used to allow platform-specific callbacks on the show event"""

    def on_hide(self):
        """Used to allow platform-specific callbacks on the hide event"""

    def validate(self, key: str) -> bool:
        """Validates a given key sequence to ensure that the key will work

        Args:
            key (str): The incoming key (without modifiers)

        Returns:
            bool: True if the key is supported, false otherwise.
        """
        return False

    def restart_app(self) -> None:
        """Performs a full restart of the application. Impl allows each platform to do this differently if needed"""
        execv(executable, [executable, *argv[1:]])


def get_platform_handler(parent: QObject) -> PlatformHandler:
    if IS_MAC:
        from plat.macos import MacOsPlatformHandler

        return MacOsPlatformHandler(parent)
    elif IS_LINUX:
        from plat.linux import LinuxPlatformHandler

        return LinuxPlatformHandler(parent)
    return PlatformHandler()
