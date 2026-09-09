"""
@author Jose Stovall | oitsjustjose
Various linux-specific handlers and helpers.
"""

from threading import Thread

from evdev import InputDevice, KeyEvent, categorize, ecodes, list_devices
from evdev.events import InputEvent
from PyQt6.QtCore import QObject

from plat import PlatformHandler

# The global keybind (with variants) for Super+Shift+\
# again, TODO: make this easily rebindable
HOTKEY_COMBOS: list[list[int]] = [
    sorted([meta, shift, ecodes.KEY_BACKSLASH]) for meta in [ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA] for shift in [ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]
]


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
        self._listener_threads: list[Thread] = []
        self.__start_threads()

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
            if combo in HOTKEY_COMBOS:
                self.on_show_signal.emit()
