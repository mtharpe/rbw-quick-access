# A wrapper around various `rbw` commands
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
        uri = uris[0] if len(uris) else None
        return BitwardenEntry(
            id=obj.get("id", ""),
            name=obj.get("name", ""),
            user=obj.get("user"),
            folder=obj.get("folder"),
            uri=uri,
            type=obj.get("type", ""),
        )


def search(query: str) -> list[BitwardenEntry]:
    try:
        output = subprocess.run(
            ["rbw", "search", "--raw", query],
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode("utf-8")

        data = json.loads(output)
        data = [BitwardenEntry.from_dict(x) for x in data]
        return data[: min(6, len(data))]
    except subprocess.CalledProcessError:
        return []
