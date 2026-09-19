import configparser
from dataclasses import dataclass
from os import makedirs
from pathlib import Path

from platformdirs import user_config_dir
from PyQt6.QtCore import QKeyCombination
from PyQt6.QtGui import QKeySequence

CURRENT_VERSION = 1

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("config").resolve()

if not Path(config_dir).exists():
    makedirs(config_dir)


@dataclass
class Keybind:
    """Defines a given trigger key and modifiers"""

    trigger: str
    ctrl: bool = False
    alt: bool = False
    meta: bool = False
    shift: bool = False

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

    @staticmethod
    def load() -> "Config":
        """Loads the config from the disk

        Returns:
            Config: The loaded config (or default)
        """

        # Create the default, save and return it
        if not conf_path.exists():
            conf = Config(
                version=CURRENT_VERSION,
                show=Keybind.deserialize("Meta+Shift+\\"),
                copy_username=Keybind.deserialize("Ctrl+C"),
                copy_password=Keybind.deserialize("Ctrl+Shift+C"),
                copy_totp=Keybind.deserialize("Alt+Shift+C"),
                open_in_browser=Keybind.deserialize("Enter"),
            )
            conf.save()
            return conf

        conf = configparser.ConfigParser()
        conf.read(conf_path)

        loaded = Config(
            version=conf.getint("general", "version"),
            show=Keybind.deserialize(conf.get("keybinds", "show")),
            copy_username=Keybind.deserialize(conf.get("keybinds", "copy_username")),
            copy_password=Keybind.deserialize(conf.get("keybinds", "copy_password")),
            copy_totp=Keybind.deserialize(conf.get("keybinds", "copy_totp")),
            open_in_browser=Keybind.deserialize(conf.get("keybinds", "open_in_browser")),
        )

        if loaded.version != CURRENT_VERSION:
            print("HANDLE ME! I'm the wrong version")

        return loaded

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
