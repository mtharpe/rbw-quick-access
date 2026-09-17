"""
@author Jose Stovall | oitsjustjose
A naive approach to config handling -- config versions aren't really handled,
    we'll just be sure to make configs backwards compatible. Or migrate them?
"""

import json
from dataclasses import dataclass
from os import makedirs
from pathlib import Path
from types import SimpleNamespace

from platformdirs import user_config_dir

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("rbw-quick-access.json").resolve()

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


@dataclass
class Keybinds:
    """Defines the full set of keybinds for the application"""

    # The keybind which controls showing the app
    show: Keybind
    # Keybinds which affect the current selection
    copy_username: Keybind
    copy_password: Keybind
    copy_totp: Keybind
    open_in_browser: Keybind


@dataclass
class Config:
    keybinds: Keybinds
    # TODO: Theme

    def save(self) -> bool:
        """Saves the given config to the user app config directory

        Returns:
            bool: returns True if the save was a success, False otherwise
        """
        try:
            with open(conf_path, "w", encoding="utf-8") as conf_fh:
                conf_fh.write(json.dumps(self, indent=2))
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
                show=Keybind(meta=True, shift=True, trigger="\\"),
                copy_username=Keybind(ctrl=True, trigger="C"),
                copy_password=Keybind(ctrl=True, shift=True, trigger="C"),
                copy_totp=Keybind(alt=True, shift=True, trigger="C"),
                open_in_browser=Keybind(trigger="Enter"),
            )
            new_conf = Config(keybinds=keybinds)
            new_conf.save()
            return new_conf

        with open(conf_path, "r", encoding="utf-8") as conf_fh:
            data: Config = json.loads(
                conf_fh.read(),
                object_hook=lambda d: SimpleNamespace(**d),
            )

        return data
