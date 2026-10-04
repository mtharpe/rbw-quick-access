"""
@author Jose Stovall | oitsjustjose

A light-weight configparser backed configuration and Config singleton
"""

import json
from os import makedirs
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import BaseModel

from config.keybind import Keybind
from plat import IS_MAC

CURRENT_VERSION = 2
CONFIG_INSTANCE = None

config_dir = user_config_dir("rbw-quick-access")
conf_path = Path(config_dir).joinpath("config.json").resolve()

if not Path(config_dir).exists():
    makedirs(config_dir)


def migrate_raw_config(raw_config: dict) -> dict:
    """Recursive method to migrate the raw JSON configuration file to the newer versions until it's up-to-date

    Args:
        raw_config (dict): The raw configuration dictionary (loaded from JSON)

    Returns:
        dict: The migrated JSON
    """

    ver: int = raw_config.get("version", 1)
    if ver == CURRENT_VERSION:
        return raw_config

    if ver == 1:
        raw_config["open_at_startup"] = False
    # As more versions come up, we can migrate them from here.
    #  Just don't forget to use elifs. I wish we had switch statements :(

    raw_config["version"] = ver + 1
    with open(conf_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(raw_config, indent=2))
    return migrate_raw_config(raw_config)


class Config(BaseModel):
    version: int
    open_at_startup: bool

    show: Keybind
    copy_username: Keybind
    copy_password: Keybind
    copy_totp: Keybind
    open_in_browser: Keybind

    def save(self):
        """Persists the current config state to disc"""
        # Since the user has opted to save, we need to be sure to commit the changes *before* saving to disk.
        self.show.commit()
        self.copy_username.commit()
        self.copy_password.commit()
        self.copy_totp.commit()
        self.open_in_browser.commit()

        with open(conf_path, "w", encoding="utf-8") as conf_fh:
            # conf_fh.write(self.model_dump_json())
            json.dump(self.model_dump(), conf_fh, indent=2)

    @staticmethod
    def get():
        """Gets the singleton config instance. If it doesn't exist yet, it's loaded"""
        global CONFIG_INSTANCE

        if CONFIG_INSTANCE is not None:
            return CONFIG_INSTANCE

        if conf_path.exists():
            with open(conf_path, "r", encoding="utf-8") as conf_fh:
                data = json.loads(conf_fh.read())
                data = migrate_raw_config(data)
            CONFIG_INSTANCE = Config(**data)
            return CONFIG_INSTANCE

        # Create the default, save and return it
        ctrl = "Meta" if IS_MAC else "Ctrl"
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
        return CONFIG_INSTANCE
