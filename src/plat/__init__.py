"""
A global, cross-platform(ish) handler for tons of things.
"""

import sys
from os import execv

from PyQt6.QtCore import QObject, pyqtSignal

IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform == "linux"


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

        # If the application has been built by PyInstaller (i.e., isn't frozen),
        #  we do / don't include the whole argv set to include `main.py`
        args = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
        # We use `execv` to essentially replace the current process, and retain the PID
        #  It also works exceptionally well with systemd, run.d, and whatever macOS uses
        execv(sys.executable, [sys.executable, *args])


def get_platform_handler(parent: QObject) -> PlatformHandler:
    if IS_MAC:
        from plat.macos import MacOsPlatformHandler

        return MacOsPlatformHandler(parent)
    elif IS_LINUX:
        from plat.linux import LinuxPlatformHandler

        return LinuxPlatformHandler(parent)
    return PlatformHandler()
