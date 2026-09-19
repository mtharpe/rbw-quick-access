"""
@author Jose Stovall | oitsjustjose
Various linux-specific handlers and helpers.
"""

from threading import Thread

from evdev import InputDevice, KeyEvent, categorize, ecodes, list_devices
from evdev.events import InputEvent
from PyQt6.QtCore import QObject

from config import Keybind, get_config
from plat import PlatformHandler

# Custom translation layer for canonical name to evdev name
EVDEV_NAMES = {
    "Enter": ecodes.KEY_ENTER,
    "Escape": ecodes.KEY_ESC,
    "Space": ecodes.KEY_SPACE,
    "Tab": ecodes.KEY_TAB,
    "Backspace": ecodes.KEY_BACKSPACE,
    "Delete": ecodes.KEY_DELETE,
    "Insert": ecodes.KEY_INSERT,
    "Home": ecodes.KEY_HOME,
    "End": ecodes.KEY_END,
    "PageUp": ecodes.KEY_PAGEUP,
    "PageDown": ecodes.KEY_PAGEDOWN,
    "Left": ecodes.KEY_LEFT,
    "Right": ecodes.KEY_RIGHT,
    "Up": ecodes.KEY_UP,
    "Down": ecodes.KEY_DOWN,
    "\\": ecodes.KEY_BACKSLASH,
}


def keybind_to_ecode(binding: Keybind) -> list[list[int]]:
    """Maps a given keybind to the ecode list equivalent
        Returns a list of keybinds, since we want to consider
        both left and right modifiers

    Args:
        binding (Keybind): The keybinding to map

    Returns:
        list[list[int]]: The fully filled set of modifiers
    """

    def __to_evdev(key: str) -> int:
        if key in EVDEV_NAMES:
            return EVDEV_NAMES[key]

        try:
            return ecodes.ecodes[f"KEY_{key.upper()}"]
        except KeyError:
            raise ValueError(f"Unsupported evdev key: {key}")

    # Use [0] as a placeholder to filter out later - if we use an empty array the list comp below fails
    ctrls = [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL] if binding.ctrl else [0]
    metas = [ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA] if binding.meta else [0]
    shifts = [ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT] if binding.shift else [0]
    alts = [ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT] if binding.alt else [0]
    keycode = __to_evdev(binding.trigger)
    # Get comprehended idiot
    comped = [[ctrl, meta, shift, alt, keycode] for ctrl in ctrls for alt in alts for meta in metas for shift in shifts]
    return [sorted(filter(lambda x: x, d)) for d in comped]


class LinuxPlatformHandler(PlatformHandler):
    """
    This class uses a DE/WM/Compositor agnostic approach to global
    keybinds, based off of [Waybind](https://github.com/postman721/Waybind).

    It works by spinning up a thread for every keyboard device and
    listening to the raw input directly, rather than depending on
    DE events or the xdg-platform nonsense which often doesn't work.
    """

    def __init__(self, parent: QObject | None) -> None:
        super().__init__(parent)
        self.__config = get_config()
        self.__activators = keybind_to_ecode(self.__config.show)
        # ALWAYS START THESE LAST IDIOT -- definitely didn't move this...
        self._listener_threads: list[Thread] = []
        self.__start_threads()

    def validate(self, key: str) -> bool:
        """Confirms that the key is valid using our custom evdev names or existing ecodes"""
        return key in EVDEV_NAMES or f"KEY_{key.upper()}" in ecodes.ecodes

    def __start_threads(self):
        """Spins up a thread for each device listening to keybinds"""

        def __is_kbd(dev: InputDevice) -> bool:
            """Performs pretty primitive checks to see if a device is a keyboard"""
            if "keyboard" in dev.name.lower():
                return True

            keys = dev.capabilities().get(ecodes.EV_KEY, [])
            return ecodes.KEY_A in keys and ecodes.KEY_ENTER in keys

        # Get _all_ devices and then filter down by capabilities
        kbd_devices: list[InputDevice[str]] = [InputDevice(p) for p in list_devices()]
        kbd_devices: list[InputDevice[str]] = list(filter(__is_kbd, kbd_devices))
        # Remap to their original paths, and spin up threads for each path
        self._listener_threads = [Thread(target=self.__read_keyboard_events, args=(dev,), daemon=True) for dev in kbd_devices]
        [thr.start() for thr in self._listener_threads]

    def __read_keyboard_events(self, dev: InputDevice):
        """Listens to all keyboard input events, filter by expected binding

        Args:
            dev (InputDevice): The input device to listen to
        """
        # Stores the current set of actively pressed keycodes
        pressed: set[int] = set()

        for raw_evt in dev.read_loop():
            # Help linting since read_loop doesn't show up in PyLance
            raw_evt: InputEvent
            if raw_evt.type != ecodes.EV_KEY:
                continue

            # Filter by event type once categorized
            key_evt = categorize(raw_evt)
            if not isinstance(key_evt, KeyEvent):
                continue

            # Key just pressed down
            if key_evt.keystate == key_evt.key_down:
                pressed.add(key_evt.scancode)
            # Key just released
            elif key_evt.keystate == key_evt.key_up:
                pressed.discard(key_evt.scancode)
            # From here, if we didn't freshly press the key,
            #  we don't really care.
            if key_evt.keystate != key_evt.key_down:
                continue

            combo = sorted(pressed)
            if combo in self.__activators:
                self.on_show_signal.emit()
