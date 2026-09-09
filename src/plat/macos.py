"""
@author Jose Stovall | oitsjustjose
Various macOS-specific handlers and helpers. Shout-out to the guy
 who sold me an M1 Mac Mini to develop this on for like $300.
"""

from pathlib import Path
from platform import machine

from PyQt6.QtCore import QObject

from plat import IS_MAC, PlatformHandler


def resolve_macos_rbw() -> str:
    """Resolves the best `rbw` build to use for macOS.
    Because we might be in-dev, we can't assume that the
      application is installed in `/opt/rbw-quick-access`,
      so we check for a dev path first, and go from there.

    Raises:
        Exception: if no valid `rbw` build could be found.

    Returns:
        str: The resolved, confirmed existing path for `rbw`
    """
    # Remap i386 to x86_64 because nothing else uses i386 >_>
    arch = "x86_64" if machine() == "i386" else machine()
    #     We use `..` here because we'll be in `src` when doing local dev
    #                  vv
    dev_build = Path(f"../rbw/{arch}/rbw")
    if dev_build.exists():
        return str(dev_build)

    release_build = Path("/usr/local/bin/rbw")
    if release_build.exists():
        return str(release_build)

    raise Exception(f"Failed to find a valid `rbw` binary!! Checked {dev_build} and {release_build}")  # noqa: TRY002


# TODO: make this super easy to rebind
#  Probably either (a) a binding of user-key to qmhk.constants.*key, or
#                  (b) maybe something exists to get the same key value?
class MacOsPlatformHandler(PlatformHandler):
    """A generic QObject to which we can attach both a qt signal and a hotkey listener to"""

    def __init__(self, parent: QObject | None) -> None:
        super().__init__(parent)

        if IS_MAC:  # TODO: is this necessary?
            from AppKit import NSApplication, NSApplicationActivationPolicyAccessory  # type: ignore
            from quickmachotkey import mask, quickHotKey
            from quickmachotkey.constants import cmdKey, kVK_ANSI_Backslash, shiftKey

            app = NSApplication.sharedApplication()
            app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

            @quickHotKey(virtualKey=kVK_ANSI_Backslash, modifierMask=mask(cmdKey, shiftKey))
            def show() -> None:
                self.on_show_signal.emit()

            # Unused, just here for the sake of avoiding GC (again T_T)
            self._show_event = show

    def on_show(self):
        if IS_MAC:
            from AppKit import NSApplication  # type:ignore[import]

            NSApplication.sharedApplication().activate()
        return super().on_show()

    def on_hide(self):
        if IS_MAC:
            from AppKit import NSApplication  # type:ignore[import]

            NSApplication.sharedApplication().deactivate()
        return super().on_hide()
