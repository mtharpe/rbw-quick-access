# RBW Quick Access

> **Fork note (mtharpe):** this fork is reworked for GNOME on Wayland. The Linux global
> hotkey no longer reads every keyboard from `/dev/input` (which needed the `input` group).
> Instead, bind a desktop shortcut to `rbw-quick-access`: the first launch starts it, and
> later launches show the running window. Copying goes through the app's own clipboard
> instead of `rbw get --clipboard`. Needs rbw 1.14+ (for `rbw search --raw`), PyQt6,
> pydantic and platformdirs; it runs from source with `python3 src/main.py`
> (`--background` starts it hidden). Upstream:
> https://git.forgeserv.cloud/oitsjustjose/rbw-quick-access

[**Demo**](https://stuff.forgeserv.cloud/Jose's%20Stuff/Screenshots/2026-09-05_09%3A01%3A32PM.mp4)

This is a tool that aims to replicate 1Password's Quick-Access overlay backed by [`rbw`](https://github.com/doy/rbw).

# Installation

## macOS

### Dependencies: [`Homebrew`](https://brew.sh/)

```bash
# Tap the self-hosted Homebrew repository:
brew tap oitsjustjose/homebrew \
 https://git.forgeserv.cloud/oitsjustjose/brew.git

# Trust the newly added Homebrew repository:
brew trust oitsjustjose/homebrew
```

Finally you can install / update super easily using:

```bash
brew install oitsjustjose/homebrew/rbw-quick-access
```

## Linux

### Dependencies: [`rbw`](https://github.com/doy/rbw)

#### Automatic Installer

This script automatically grabs the latest release and can be re-run whenever you'd like to update. It's compatible with `systemd`, and it _should_ be compatible with `OpenRC` and `runit`, but I don't have machines with either so I went off documentation alone. **The installer requires `jq` and either `curl` or `wget`**

```bash
curl -sL https://git.forgeserv.cloud/oitsjustjose/rbw-quick-access/raw/branch/main/scripts/install.linux.sh | sh
# or for wget users:
wget -q -O - https://git.forgeserv.cloud/oitsjustjose/rbw-quick-access/raw/branch/main/scripts/install.linux.sh | sh
```

#### Manual Installation

1.  Grab the `linux` build from the [latest release](https://git.forgeserv.cloud/oitsjustjose/rbw-quick-access/releases/latest)
2.  Untar the release using `tar -xzvf {file}`
3.  Move `rbw-quick-access` and `_internal` to some shared directory (like `/opt/rbw-quick-access`).
4.  Set it up however you like with your `init` system of choice!

## Windows

### 🚫 Windows is not and will not be supported 🚫

While this is partially a personal decision (all of my daily-drivers run Linux), the fundamental issue is that `rbw` is built for and around `POSIX` systems.

I could, theoretically, write a botched version of `rbw-quick-access` using the `bw` cli, but to be frank the `bw` cli isn't nearly as performant and requires a your vault key every time you list/get/search in it.

# Post-Install

## `rbw` Configuration

Once you have everything installed, configure `rbw` so it knows where your vault is and who you are with the various options. See the [official `rbw` docs](https://github.com/doy/rbw#configuration) on what config options you have.

**At the very least you must configure `email` with `rbw config set email <your email>`.**

# Limitations

Currently there's one particularly big limitation that I can't fix without killing performance: `rbw` **also shows archived items**. The best route is to make sure your archive isn't massive (mine was in the demo above, as I'd just moved from 1Password and it brought over those items).

If you need to clear out your archived items, you'll have to do it from the Vaultwarden web ui (limited at 500 items at a time), Bitwarden doesn't offer a mass-select-and-trash option. Don't forget to refresh your Bitwarden before proceeding.

# Design Goals

## Quick Startup

## Large Dataset Support

Using PyQT6's delegate, events, and sticking with primitives where possible, the password list is able to easily handle hundreds of thousands of secrets from your vault just like that! 🫰

## Parity with 1Password

When designing this, I was moving from 1Password after using it for 8+ years straight. Moving to [Vault|Bit]warden was mostly a breeze, but this was the one and only working flow that was broken up entirely.

### Fields

To succeed in replicating the feel (and more importantly, functionality) of the 1Password quick-access app(let?). The biggest things were being able to search by, and see, the following when browsing and searching:

-   Entry Name
-   Website
-   Username

### Keyboard Shortcuts

After 8 years with this system, the keyboard shortcuts were pretty well engrained in my head

-   Show the application with:
    -   <kbd>super</kbd> + <kbd>shift</kbd> + <kbd>\\</kbd>
    -   <kbd>cmd</kbd> + <kbd>shift</kbd> + <kbd>\\</kbd>
    -   <kbd>win</kbd> + <kbd>shift</kbd> + <kbd>\\</kbd>
-   `enter` opens the URL, if there is one.
-   ~~`alt + enter` does the same? I'm not sure why...~~ since this was redundant, I didn't bother
-   `ctrl + c` copies the username (if present)
-   `ctrl + shift + c` copies the password
-   `ctrl + alt + c` copies the TOTP
-   `ctrl + o` - NOOP; this opens the item in a new window. I don't want to deal with integrating with the BitWarden GUI too...
-   `ctrl + shift + o` - also NOOP; this opens the item in the full 1Password window, not just the viewer window, and that's just not gonna happen...

# Milestones:

-   [ ] Improved settings GUI
-   [ ] Customization
    -   [ ] Color Themes
    -   [ ] Advanced color customization (pick your own hex, etc.)
    -   [ ] Font selections (for `gui.SearchResults`, `gui.HotkeyGuide`, and general text throughout the GUI)
