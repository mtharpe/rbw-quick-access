"""
@author Jose Stovall | oitsjustjose

A wrapper around the various rbw commands, including caching for better performance
"""

import json
from dataclasses import dataclass
from subprocess import PIPE, CalledProcessError, run

from plat import IS_MAC

RBW: str = "rbw"
if IS_MAC:
    from plat.macos import resolve_macos_rbw

    # Since we use a dynamic `rbw` executable (thanks to the macOS build being slow), we have to determine it now.
    RBW = resolve_macos_rbw()


@dataclass
class BitwardenEntry:
    id: str
    name: str
    user: str | None
    folder: str | None
    uri: str | None
    type: str

    @staticmethod
    def from_dict(obj: dict) -> "BitwardenEntry":
        uris = obj.get("uris", [])
        uri = uris[0] if uris else None
        return BitwardenEntry(
            id=obj.get("id", ""),
            name=obj.get("name", ""),
            user=obj.get("user"),
            folder=obj.get("folder"),
            uri=uri,
            type=obj.get("type", ""),
        )


def search(query: str, limit: int | None = None) -> list[BitwardenEntry] | None:
    """Performs the `rbw` search with the given query, limited by a number of results defined

    Args:
        query (str): The query which is passed to `rbw search`
        limit (int, optional): The amount of entries to limit to. Defaults to 6.

    Returns:
        list[BitwardenEntry] | None: A list of bitwarden entries found, or None if an error occurred
    """
    try:
        output = run([RBW, "search", "--raw", query], stdout=PIPE, check=True).stdout.decode("utf-8")

        data = [BitwardenEntry.from_dict(x) for x in json.loads(output)]
        return data[: min(limit or 1_000_000, len(data))]
    except CalledProcessError:
        return None


def copy_username(entry: BitwardenEntry):
    try:
        run([RBW, "get", entry.id, "--field", "username", "--clipboard"], check=True)
    except CalledProcessError:
        return


def copy_password(entry: BitwardenEntry):
    try:
        run([RBW, "get", entry.id, "--field", "password", "--clipboard"], check=True)
    except CalledProcessError:
        return


def copy_totp(entry: BitwardenEntry):
    try:
        run([RBW, "get", entry.id, "--field", "totp", "--clipboard"], check=True)
    except CalledProcessError:
        return


def unlock():
    """Runs `rbw login` to refresh login state"""
    try:
        run([RBW, "unlock"], check=True)
        return True
    except CalledProcessError:
        return False
