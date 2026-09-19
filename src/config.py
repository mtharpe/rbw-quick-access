"""
@author Jose Stovall | oitsjustjose
A naive approach to config handling with versioning -- ish?
"""

import json
from dataclasses import dataclass
from os import makedirs
from pathlib import Path

from dataclass_wizard import JSONWizard
from platformdirs import user_config_dir
from PyQt6.QtCore import Qt

CURRENT_VERSION = 1

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("rbw-quick-access.json").resolve()

if not Path(config_dir).exists():
    makedirs(config_dir)


@dataclass
class Keybind(JSONWizard):
    """Defines a given trigger key and modifiers"""

    trigger: str
    ctrl: bool = False
    alt: bool = False
    meta: bool = False
    shift: bool = False

    @staticmethod
    def from_text(text_repr: str) -> "Keybind":
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

    def to_text(self) -> str:
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

    def matches(self, keycode: int, mods: Qt.KeyboardModifier) -> bool:
        """Determines if the incoming key and modifiers match this one

        Args:
            key (Qt.Key): The main key pressed (matches to `ord(self.trigger.upper()`) usually)
            mods (Qt.KeyboardModifier): The modifiers that were pressed at the time

        Returns:
            bool: True if the key and mods match
        """

        if self.trigger != keycode:
            return False

        modifiers = Qt.KeyboardModifier.NoModifier
        if self.ctrl:
            modifiers |= Qt.KeyboardModifier.ControlModifier
        if self.alt:
            modifiers |= Qt.KeyboardModifier.AltModifier
        if self.meta:
            modifiers |= Qt.KeyboardModifier.MetaModifier
        if self.shift:
            modifiers |= Qt.KeyboardModifier.ShiftModifier

        return mods == modifiers


@dataclass
class Keybinds(JSONWizard):
    """Defines the full set of keybinds for the application"""

    # The keybind which controls showing the app
    show: Keybind
    # Keybinds which affect the current selection
    copy_username: Keybind
    copy_password: Keybind
    copy_totp: Keybind
    open_in_browser: Keybind


@dataclass
class Config(JSONWizard):
    keybinds: Keybinds
    version: int = 0
    # TODO: Theme

    def save(self) -> bool:
        """Saves the given config to the user app config directory

        Returns:
            bool: returns True if the save was a success, False otherwise
        """
        try:
            with open(conf_path, "w", encoding="utf-8") as conf_fh:
                conf_fh.write(json.dumps(self.to_dict(), indent=2))
        except Exception as e:  # noqa: BLE001
            print(e)
            return False

        return True

    @staticmethod
    def load() -> "Config":
        """Loads the config if one exists - if it doesn't then a new one is generated
        Loading is handled using SimpleNamespace which makes creating a dataclass from
        JSON super easy <3

        Returns:
            Config: The (newly generated or existing) config
        """

        if not conf_path.exists():
            keybinds = Keybinds(
                show=Keybind.from_text("Meta+Shift+\\"),
                copy_username=Keybind.from_text("Ctrl+C"),
                copy_password=Keybind.from_text("Ctrl+Shift+C"),
                copy_totp=Keybind.from_text("Alt+Shift+C"),
                open_in_browser=Keybind.from_text("Enter"),
            )
            new_conf = Config(version=CURRENT_VERSION, keybinds=keybinds)
            new_conf.save()
            return new_conf

        with open(conf_path, "r", encoding="utf-8") as conf_fh:
            config = Config.from_dict(json.loads(conf_fh.read()))

        if config.version != CURRENT_VERSION:
            print(f"Config version is {config.version} - not {CURRENT_VERSION} -- need to migrate it!")

        return config
