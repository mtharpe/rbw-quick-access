"""
@author Jose Stovall | oitsjustjose
Various linux-specific handlers and helpers.
"""

from plat import PlatformHandler


class LinuxPlatformHandler(PlatformHandler):
    """
    Linux leaves the global "show" shortcut to the desktop: bind a shortcut (e.g. in GNOME
    Settings > Keyboard > Custom Shortcuts) to `rbw-quick-access`. A second launch tells the
    running instance to show itself (see instance.py).

    This replaces reading every keyboard straight from /dev/input, which needed the user in
    the `input` group and so let any of their programs read all keystrokes.
    """
