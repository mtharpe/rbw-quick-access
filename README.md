# RBW Quick Access

This is a tool that aims to replicate 1Password's Quick-Access overlay backed by [`rbw`](https://github.com/doy/rbw).

# Skip straight to the [Downloads](https://git.oitsjustjose.com/me/rbw-quick-access/-/releases)

# Demo

![](https://stuff.forgeserv.cloud/Jose's%20Stuff/Screenshots/2026-09-05_09%3A01%3A32PM.mp4)

# Limitations

Currently there's one particularly big limitation that I can't fix without killing performance: `rbw` **also shows archived items**. The best route is to make sure your archive isn't massive (mine was in the demo above, as I'd just moved from 1Password and it brought over those items).

If you need to clear out your archived items, you'll have to do it from the Vaultwarden web ui (limited at 500 items at a time), Bitwarden doesn't offer a mass-select-and-trash option. Don't forget to refresh your BItwarden before proceeding.

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

# Dependencies

## Linux

-   `rbw`

## macOS

**[`brew`](https://brew.sh/) for macOS users**. A custom build of `rbw` is provided with the artifacts (see `rbw/README.md` for more info why).

# Installation

## The Easy Part

Installation is super easy -- download the right file for your distro and machine, untar the file, and run the provided `.sh` script which should handle the installation for you. If you have any issues, let me know -- but please check #Dependencies first and make sure you aren't missing one!

## `rbw` Configuration

Once you have everything installed, configure `rbw` so it knows where your vault is and who you are with the various options. See the [official `rbw` docs](https://github.com/doy/rbw#configuration) on what config options you have, but at the very least you must configure `email` with `rbw config set email <your email>`.

# Milestones:

-   [x] The next big milestone is to re-architect the app such that it stays alive between launches, such that running `rbw-quick-access --show` (or something to that effect) will spin up a singleton if it isn't running, and shows it. This would mean a single binary file is all I'd need to distribute and would make installation easier.
-   [x] ~~Windows~~ & macOS Builds
    -   Skipping Windows for now. I frankly don't feel like it - especially since `rbw` isn't natively supported there. Who knows how painful getting it build with `cargo` .
-   [ ] 1Password's Quick Access clears the search field & results after some given amount of time. It otherwise keeps the previous selection active. I want to implement the same.
-   [ ] Eventually we'll want a configuration screen which:
    -   [ ] Would allow you to select a vault
    -   [ ] ..or a specific folder
    -   [ ] Change sorting methods (like sorting by most-used)
    -   [ ] Change the in-app keyboard shortcuts
    -   [ ] or the various colors
    -   [ ] or the font
