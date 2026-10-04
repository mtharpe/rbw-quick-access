"""
@author Jose Stovall | oitsjustjose
Various macOS-specific handlers and helpers. Shout-out to the guy
 who sold me an M1 Mac Mini to develop this on for like $300.
"""

from pathlib import Path
from platform import machine
from typing import TYPE_CHECKING

import quickmachotkey.constants as c  # type: ignore
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory, NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorFullScreenAuxiliary, NSWorkspace  # type: ignore
from objc import objc_object  # type: ignore
from quickmachotkey import mask, quickHotKey  # type: ignore

from config import Config
from plat import PlatformHandler

if TYPE_CHECKING:
    from gui import MainWindow

# This thing fucking sucks. I hate keybinds.
MISERABLE_MAPPER = {
    # Symbols
    "-": c.kVK_ANSI_Minus,
    ",": c.kVK_ANSI_Comma,
    ";": c.kVK_ANSI_Semicolon,
    ".": c.kVK_ANSI_Period,
    "'": c.kVK_ANSI_Quote,
    "[": c.kVK_ANSI_LeftBracket,
    "]": c.kVK_ANSI_RightBracket,
    "/": c.kVK_ANSI_Slash,
    "\\": c.kVK_ANSI_Backslash,
    "`": c.kVK_ANSI_Grave,
    "=": c.kVK_ANSI_Equal,
    # Alphanum
    "0": c.kVK_ANSI_0,
    "1": c.kVK_ANSI_1,
    "2": c.kVK_ANSI_2,
    "3": c.kVK_ANSI_3,
    "4": c.kVK_ANSI_4,
    "5": c.kVK_ANSI_5,
    "6": c.kVK_ANSI_6,
    "7": c.kVK_ANSI_7,
    "8": c.kVK_ANSI_8,
    "9": c.kVK_ANSI_9,
    "A": c.kVK_ANSI_A,
    "B": c.kVK_ANSI_B,
    "C": c.kVK_ANSI_C,
    "D": c.kVK_ANSI_D,
    "E": c.kVK_ANSI_E,
    "F": c.kVK_ANSI_F,
    "G": c.kVK_ANSI_G,
    "H": c.kVK_ANSI_H,
    "I": c.kVK_ANSI_I,
    "J": c.kVK_ANSI_J,
    "K": c.kVK_ANSI_K,
    "L": c.kVK_ANSI_L,
    "M": c.kVK_ANSI_M,
    "N": c.kVK_ANSI_N,
    "O": c.kVK_ANSI_O,
    "P": c.kVK_ANSI_P,
    "Q": c.kVK_ANSI_Q,
    "R": c.kVK_ANSI_R,
    "S": c.kVK_ANSI_S,
    "T": c.kVK_ANSI_T,
    "U": c.kVK_ANSI_U,
    "V": c.kVK_ANSI_V,
    "W": c.kVK_ANSI_W,
    "X": c.kVK_ANSI_X,
    "Y": c.kVK_ANSI_Y,
    "Z": c.kVK_ANSI_Z,
    # Function Keys
    "F1": c.kVK_F1,
    "F2": c.kVK_F2,
    "F3": c.kVK_F3,
    "F4": c.kVK_F4,
    "F5": c.kVK_F5,
    "F6": c.kVK_F6,
    "F7": c.kVK_F7,
    "F8": c.kVK_F8,
    "F9": c.kVK_F9,
    "F10": c.kVK_F10,
    "F11": c.kVK_F11,
    "F12": c.kVK_F12,
    "F13": c.kVK_F13,
    "F14": c.kVK_F14,
    "F15": c.kVK_F15,
    "F16": c.kVK_F16,
    "F17": c.kVK_F17,
    "F18": c.kVK_F18,
    "F19": c.kVK_F19,
    "F20": c.kVK_F20,
    # Special
    "Backspace": c.kVK_Delete,
    "Delete": c.kVK_ForwardDelete,
    "Enter": c.kVK_Return,
    "Return": c.kVK_Return,
    "Escape": c.kVK_Escape,
    "Space": c.kVK_Space,
    "Tab": c.kVK_Tab,
    # Arrow Keys
    "Up": c.kVK_UpArrow,
    "Down": c.kVK_DownArrow,
    "Left": c.kVK_LeftArrow,
    "Right": c.kVK_RightArrow,
    # Other Nav
    "Home": c.kVK_Home,
    "End": c.kVK_End,
    "PageUp": c.kVK_PageUp,
    "PageDown": c.kVK_PageDown,
}


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


class MacOsPlatformHandler(PlatformHandler):
    """A generic QObject to which we can attach both a qt signal and a hotkey listener to"""

    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.__config = Config.get()
        self.__app = NSApplication.sharedApplication()
        self.__app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        self.__main_window = parent
        self.__previous_app = None

        @quickHotKey(virtualKey=self.__get_virt_key(), modifierMask=mask(*self.__get_modifier_mask()))
        def show() -> None:
            self.on_show_signal.emit()

        # Unused, just here for the sake of avoiding GC (again T_T)
        self._show_event = show

    def configure_window(self) -> None:
        """Performs custom configuration to make the overlay behave like one"""
        # Apparently this forces QT to make a native window. Huh.
        win_id = int(self.__main_window.winId())
        view = objc_object(c_void_p=win_id)
        window = view.window()

        window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary)

    def on_show(self):
        """Grabs the previously active application and stores it for later"""
        app = NSApplication.sharedApplication()

        if not app.isActive():
            frontmost = NSWorkspace.sharedWorkspace().frontmostApplication()
            # Frontmost can be falsy but None is the definitive answer here
            if frontmost is not None:
                self.__previous_app = frontmost

        app.activate()
        return super().on_show()

    def on_hide(self):
        """Restores focus to the previously focused application, if applicable"""
        if self.__previous_app is not None:
            self.__previous_app.activateWithOptions_(0)
            self.__previous_app = None
        return super().on_hide()

    def validate(self, key: str) -> bool:
        """Even easier since the mapper has already made our lives miserable enough"""
        return key in MISERABLE_MAPPER

    def __get_virt_key(self) -> c.VirtualKey:
        """Gets the virtual key corresponding to the key trigger"""
        uppies = self.__config.show.trigger.upper()
        if uppies not in MISERABLE_MAPPER:
            raise KeyError
        return MISERABLE_MAPPER[uppies]

    def __get_modifier_mask(self) -> list[c.ModifierKey]:
        """Builds out the modifier mask list from the keybind"""
        modifiers: list[c.ModifierKey] = []
        if self.__config.show.ctrl:
            modifiers.append(c.controlKey)

        if self.__config.show.alt:
            modifiers.append(c.optionKey)

        if self.__config.show.meta:
            modifiers.append(c.cmdKey)

        if self.__config.show.shift:
            modifiers.append(c.shiftKey)

        return modifiers
