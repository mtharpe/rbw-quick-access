from quickmachotkey import mask, quickHotKey
from quickmachotkey.constants import cmdKey, kVK_ANSI_Backslash, shiftKey


@quickHotKey(virtualKey=kVK_ANSI_Backslash, modifierMask=mask(cmdKey, shiftKey))
def handler() -> None:
    print("hi mom :)")


if __name__ == "__main__":
    from AppKit import NSApplication  # type:ignore[import]
    from PyObjCTools import AppHelper  # type:ignore[import]

    print("type ⌘⌃⌥X with any application focused")
    NSApplication.sharedApplication()
    AppHelper.runEventLoop()
