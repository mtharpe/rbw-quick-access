"""
@author Jose Stovall | oitsjustjose

A wrapper around the various rbw commands, including caching for better performance
"""

import json
from dataclasses import dataclass
from shutil import which
from subprocess import PIPE, CalledProcessError, run


class RbwNotFoundException(Exception):
    def __init__(self, *args: object):
        super().__init__(args)


def __get_rbw() -> str:
    """Gets the RBW instance to see

    Raises:
        RbwNotFoundException:  to track down

    Returns:
        str: The path
    """
    rbw: str | None = which("rbw")
    if not rbw:
        raise RbwNotFoundException()
    return rbw


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
        output = run([__get_rbw(), "search", "--raw", query], stdout=PIPE, check=True).stdout.decode("utf-8")

        data = [BitwardenEntry.from_dict(x) for x in json.loads(output)]
        return data[: min(limit or 1_000_000, len(data))]
    except CalledProcessError:
        return None


def copy_username(entry: BitwardenEntry):
    try:
        run([__get_rbw(), "get", entry.id, "--field", "username", "--clipboard"], check=True)
    except CalledProcessError:
        return


def copy_password(entry: BitwardenEntry):
    try:
        run([__get_rbw(), "get", entry.id, "--field", "password", "--clipboard"], check=True)
    except CalledProcessError:
        return


def copy_totp(entry: BitwardenEntry):
    try:
        run([__get_rbw(), "get", entry.id, "--field", "totp", "--clipboard"], check=True)
    except CalledProcessError:
        return


def login():
    """Runs `rbw login` to refresh login state"""
    try:
        run([__get_rbw(), "login"], check=True)
        return True
    except CalledProcessError:
        return False


def unlock():
    """Runs `rbw unlock` to allow searching & copying"""
    try:
        run([__get_rbw(), "unlock"], check=True)
        return True
    except CalledProcessError:
        return False
