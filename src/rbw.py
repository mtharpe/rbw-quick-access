"""
@author Jose Stovall | oitsjustjose

A wrapper around the various rbw commands, including caching for better performance
"""

import json
import subprocess
from dataclasses import dataclass


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


def search(query: str, limit=6) -> list[BitwardenEntry] | None:
    """Performs the `rbw` search with the given query, limited by a number of results defined

    Args:
        query (str): The query which is passed to `rbw search`
        limit (int, optional): The amount of entries to limit to. Defaults to 6.

    Returns:
        list[BitwardenEntry] | None: A list of bitwarden entries found, or None if an error occurred
    """
    try:
        output = subprocess.run(
            ["rbw", "search", "--raw", query],
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode("utf-8")

        data = [BitwardenEntry.from_dict(x) for x in json.loads(output)]
        return data[: min(limit, len(data))]
    except subprocess.CalledProcessError:
        return None
