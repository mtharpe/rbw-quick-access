from pathlib import Path
from platform import mac_ver, machine

IS_MAC = bool(mac_ver()[0])


def resolve_macos_rbw() -> str:
    """Resolves the best `rbw` build to use for macOS.
    Because we might be in-dev, we can't assume that the
      application is installed in `/opt/rbw-quick-access`,
      so we check for a dev path first, and go from there.

    Raises:
        Exception: if no valid `rbw` build could be found.

    Returns:
        str: The resolved, confirmed existing path for `rbw`
    """
    #     We use `..` here because we'll be in `src` when doing local dev
    #                  vv
    dev_build = Path(f"../rbw/{machine()}/rbw")
    if dev_build.exists():
        return str(dev_build)

    release_build = Path("/opt/rbw-quick-access/rbw")
    if release_build.exists():
        return str(release_build)

    raise Exception(f"Failed to find a valid `rbw` binary!! Checked {dev_build} and {release_build}")  # noqa: TRY002
