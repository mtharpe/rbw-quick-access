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

CURRENT_VERSION = 1

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("config").resolve()

if not Path(config_dir).exists():
    makedirs(config_dir)


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
        # Why reinvent the wheel - str(self) uses the nicely defined creator below
        self_seq = QKeySequence.fromString(str(self), QKeySequence.SequenceFormat.PortableText)
        return self_seq.matches(QKeySequence(combo)) == QKeySequence.SequenceMatch.ExactMatch

    def set(self, new_sequence: QKeySequence):
        """Called when changed by the QT GUI

        Args:
            new_sequence (QKeySequence): The new keybind sequence
        """
        # Make a full backup
        self.original = Keybind.deserialize(str(self))

        # The QT key format here is.... weird. This was easiest.
        as_str = new_sequence.toString(QKeySequence.SequenceFormat.PortableText)
        new_kb = Keybind.deserialize(as_str)

        self.trigger = new_kb.trigger
        self.ctrl = new_kb.ctrl
        self.alt = new_kb.alt
        self.meta = new_kb.meta
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

    def __str__(self):
        """Creates a string repr of the keybind

        Returns:
            str: A string repr of the keybind, compatible as an input to Keybind::from_text
        """

        return "+".join(
            filter(
                bool,
                [
                    "Ctrl" if self.ctrl else "",
                    "Alt" if self.alt else "",
                    "Meta" if self.meta else "",
                    "Shift" if self.shift else "",
                    self.trigger,
                ],
            )
        )


@dataclass
class Config:
    version: int

    show: Keybind
    copy_username: Keybind
    copy_password: Keybind
    copy_totp: Keybind
    open_in_browser: Keybind

    def save(self):
        """Persists the current config state to disc"""
        conf = configparser.ConfigParser()
        conf["general"] = {"version": str(self.version)}
        conf["keybinds"] = {
            "show": str(self.show),
            "copy_username": str(self.copy_username),
            "copy_password": str(self.copy_password),
            "copy_totp": str(self.copy_totp),
            "open_in_browser": str(self.open_in_browser),
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

    if not CONFIG_INSTANCE:
        # Create the default, save and return it
        if not conf_path.exists():
            CONFIG_INSTANCE = Config(
                version=CURRENT_VERSION,
                show=Keybind.deserialize("Meta+Shift+\\"),
                copy_username=Keybind.deserialize("Ctrl+C"),
                copy_password=Keybind.deserialize("Ctrl+Shift+C"),
                copy_totp=Keybind.deserialize("Alt+Shift+C"),
                open_in_browser=Keybind.deserialize("Enter"),
            )
            CONFIG_INSTANCE.save()

        else:
            parser = configparser.ConfigParser()
            parser.read(conf_path)

            CONFIG_INSTANCE = Config(
                version=parser.getint("general", "version"),
                show=Keybind.deserialize(parser.get("keybinds", "show")),
                copy_username=Keybind.deserialize(parser.get("keybinds", "copy_username")),
                copy_password=Keybind.deserialize(parser.get("keybinds", "copy_password")),
                copy_totp=Keybind.deserialize(parser.get("keybinds", "copy_totp")),
                open_in_browser=Keybind.deserialize(parser.get("keybinds", "open_in_browser")),
            )

            if CONFIG_INSTANCE.version != CURRENT_VERSION:
                print("HANDLE ME! I'm the wrong version")

    return CONFIG_INSTANCE
