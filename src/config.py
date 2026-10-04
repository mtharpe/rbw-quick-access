"""
@author Jose Stovall | oitsjustjose

A light-weight configparser backed configuration and Config singleton
"""

import configparser
from dataclasses import dataclass
from os import makedirs
from pathlib import Path

from platformdirs import user_config_dir
from PyQt6.QtCore import QKeyCombination, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence

from plat import IS_MAC

CURRENT_VERSION = 1

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("config").resolve()

if not Path(config_dir).exists():
    makedirs(config_dir)


class ConfigParser(configparser.ConfigParser):
    """A custom config parser implementation which has default support"""

    def __init__(self):
        super().__init__()

    def get_int_or_default(self, section: str, option: str, default: int) -> int:
        if not self.has_option(section, option):
            return default
        return self.getint(section, option)

    def get_float_or_default(self, section: str, option: str, default: float) -> float:
        if not self.has_option(section, option):
            return default
        return self.getfloat(section, option)


class Keybind(QObject):
    """Defines a given trigger key and modifiers"""

    # Called when restored so the config GUI updates
    on_restored = pyqtSignal()

    def __init__(self, trigger: str, ctrl: bool = False, alt: bool = False, meta: bool = False, shift: bool = False):
        super().__init__()
        self.trigger = trigger
        self.ctrl = ctrl
        self.alt = alt
        self.meta = meta
        self.shift = shift

        self.original: Keybind | None = None

    @staticmethod
    def deserialize(text_repr: str) -> "Keybind":
        """Converts a text-based shortcut (like "Ctrl+A") into
        a proper Keybind entry

        Args:
            text_repr (str): The text representation, as obtained by ::to_text

        Returns:
            Keybind: The built keybind
        """
        parts = text_repr.lower().split("+")

        ctrl = "ctrl" in parts
        alt = "alt" in parts
        meta = "meta" in parts
        shift = "shift" in parts
        trigger = parts[-1]

        return Keybind(
            trigger,
            ctrl=ctrl,
            alt=alt,
            meta=meta,
            shift=shift,
        )

    def qt_matches(self, combo: QKeyCombination) -> bool:
        """Determines if a given key combination matches this keybind

        Args:
            combo (QKeyCombination): The QT Key Combination coming in

        Returns:
            bool: True if the key combo is an exact match
        """
        # Why reinvent the wheel - self.to_string uses the nicely defined creator below
        self_seq = QKeySequence.fromString(self.to_string(qt_fmt=True), QKeySequence.SequenceFormat.PortableText)
        return self_seq.matches(QKeySequence(combo)) == QKeySequence.SequenceMatch.ExactMatch

    def set(self, new_sequence: QKeySequence):
        """Called when changed by the QT GUI

        Args:
            new_sequence (QKeySequence): The new keybind sequence
        """
        # Make a full backup
        self.original = Keybind.deserialize(self.to_string())

        # The QT key format here is.... weird. This was easiest.
        as_str = new_sequence.toString(QKeySequence.SequenceFormat.PortableText)
        new_kb = Keybind.deserialize(as_str)

        self.trigger = new_kb.trigger
        # Swap out meta and ctrl for macOS
        self.ctrl = new_kb.meta if IS_MAC else new_kb.ctrl
        self.meta = new_kb.ctrl if IS_MAC else new_kb.meta
        self.alt = new_kb.alt
        self.shift = new_kb.shift

    def restore(self):
        """Resets any changes to the keybind"""
        if not self.original:
            return

        self.trigger = self.original.trigger
        self.ctrl = self.original.ctrl
        self.alt = self.original.alt
        self.meta = self.original.meta
        self.shift = self.original.shift
        self.original = None
        self.on_restored.emit()

    def to_string(self, qt_fmt=False) -> str:
        """Creates a (QT-compatible if set) string from this keybind"""
        ctrl = self.meta if (qt_fmt and IS_MAC) else self.ctrl
        meta = self.ctrl if (qt_fmt and IS_MAC) else self.meta

        return "+".join(
            filter(
                bool,
                [
                    "Ctrl" if ctrl else "",
                    "Alt" if self.alt else "",
                    "Meta" if meta else "",
                    "Shift" if self.shift else "",
                    self.trigger,
                ],
            )
        )

    def __str__(self) -> str:
        return self.to_string()


@dataclass
class Config:
    version: int
    open_at_startup: bool

    show: Keybind
    copy_username: Keybind
    copy_password: Keybind
    copy_totp: Keybind
    open_in_browser: Keybind

    def save(self):
        """Persists the current config state to disc"""
        conf = configparser.ConfigParser()
        conf["general"] = {
            "version": str(self.version),
            "open_at_startup": str(self.open_at_startup),
        }

        conf["keybinds"] = {
            "show": self.show.to_string(),
            "copy_username": self.copy_username.to_string(),
            "copy_password": self.copy_password.to_string(),
            "copy_totp": self.copy_totp.to_string(),
            "open_in_browser": self.open_in_browser.to_string(),
        }

        with open(conf_path, "w", encoding="utf-8") as conf_fh:
            conf.write(conf_fh)

        # Since we've saved, cancelling should remove the "originals"
        self.show.original = None
        self.copy_username.original = None
        self.copy_password.original = None
        self.copy_totp.original = None
        self.open_in_browser.original = None


CONFIG_INSTANCE: Config | None = None


def get_config() -> Config:
    """Gets the singleton config instance. If it doesn't exist yet, it's loaded"""
    global CONFIG_INSTANCE

    ctrl = "Meta" if IS_MAC else "Ctrl"

    if not CONFIG_INSTANCE:
        # Create the default, save and return it
        if not conf_path.exists():
            CONFIG_INSTANCE = Config(
                version=CURRENT_VERSION,
                open_at_startup=False,
                show=Keybind.deserialize("Meta+Shift+\\"),
                copy_username=Keybind.deserialize(f"{ctrl}+C"),
                copy_password=Keybind.deserialize(f"{ctrl}+Shift+C"),
                copy_totp=Keybind.deserialize("Alt+Shift+C"),
                open_in_browser=Keybind.deserialize("Enter"),
            )
            CONFIG_INSTANCE.save()

        else:
            parser = configparser.ConfigParser()
            parser.read(conf_path)

            CONFIG_INSTANCE = Config(
                version=parser.getint("general", "version"),
                open_at_startup=parser.getboolean("general", "open_at_startup"),
                show=Keybind.deserialize(parser.get("keybinds", "show")),
                copy_username=Keybind.deserialize(parser.get("keybinds", "copy_username")),
                copy_password=Keybind.deserialize(parser.get("keybinds", "copy_password")),
                copy_totp=Keybind.deserialize(parser.get("keybinds", "copy_totp")),
                open_in_browser=Keybind.deserialize(parser.get("keybinds", "open_in_browser")),
            )

            if CONFIG_INSTANCE.version != CURRENT_VERSION:
                print("HANDLE ME! I'm the wrong version")

    return CONFIG_INSTANCE
