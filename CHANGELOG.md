# 1.0.0

Alright, I've been using this tool on macOS and Linux for weeks now, I think it's time to call this an official 1.0.0 release! Just bugfixes that I've been noting as I use it:

### Changed

-   Changes made to your vault will be synced when the window is closed 
    -   It's a slow process, so it's done in a background thread 
-   The currently selected item will be unfocused and the searchbox fully selected when at least 30 seconds have elapsed since you last hid the window
    -   This lets you pick up where you left off if you're having to manually copy username | password | totp, without it being obnoxious and persist forever.
-   Clicking or tabbing out of the `rbw-quick-access` window now hides the window.

### Fixed

-   On each show, does a check to ensure that `rbw` is unlocked, prompting you for your vault password **before** showing the window.
    -   This prevents you from typing out your whole search prompt and then getting a `pinentry` window asking for your Bitwarden vault password **for each character you typed**. That was a pain.

# 0.0.4

## The Configuration Update!

This was long overdue -- there's still not an in-application GUI for the config, but this is better than nothing for the time being. After updating, you'll be able to hit <kbd>Ctrl</kbd>+<kbd>,</kbd> (<kbd>Cmd</kbd>+<kbd>,</kbd> for macOS users) to open the settings window.

To keep things easy on me (since this is something you won't change often), modifying the keybinds will require an application restart.

**Known Bug**: For whatever reason, QT (the GUI backend for `rbw-quick-access`) doesn't allow you to just use a single key as a keybind. The application will let you set the keybind for copying something to, say, <kbd>A</kbd>, but it won't work.

### Added

-   Settings GUI -- open with <kbd>Ctrl</kbd>+<kbd>,</kbd> (<kbd>Cmd</kbd>+<kbd>,</kbd> for macOS users)
-   Ability to modify the keybinds for:
    -   Showing the application
    -   Opening the URL for a given entry
    -   Copying the Username for a given entry
    -   Copying the Password for a given entry
    -   Copying the TOTP for a given entry
-   Configuration file at `%user_config_dir%/rbw-quick-access/config`

### Fixed

-   If the window was already shown, but backgrounded, the show keybind wouldn't bring it back to the front.
-   [macOS] Opening Quick Access while in a full-screen application would take you out of the fullscreen application to show
-   [macOS] Exiting out of Quick Access wouldn't return focus to your previous window
-   [macOS] When the launcher starts at login, a terminal window would appear for the application
    -   This requires removing the old startup item, and adding an agent
    -   This isn't a huge deal, but you'll now see the startup agent alert

# 0.0.3

This update was a huge pain and required me to buy a Mac just to get here. But! In exchange, you get a Mac port. 

If you like this enough, feel free to throw cash my way on [Kofi](https://ko-fi.com/oitsjustjose)? Absolutely no pressure though - I do this for the love of the game.

## macOS Port

WOOF - this was a rough one. I ran into so many challenges along the way:

-   Didn't have a Mac to do builds on
    -   Especially not one with a new enough processor for QT6. My newest one is a 2014 MBP
    -   Shout out to the guy on FB Marketplace selling an M1 Mini exactly when I needed it.
-   `rbw` build was drastically slow on macOS - had to compile my own build from a combination of two different changes (see rbw/README.md). JUST for macOS -- Linux works amazingly. On Linux, searching/loading the list took ~0.02s. On macOS the same operation was taking 3-5 **seconds**. Now it's just about instant -- or at least, liveably fast.
-   Had to fully re-do the build scripts and install scripts for both Linux and macOS to support/ignore the various macOS-specific flags and steps
-   Global keybind implementation was necessary to get this to work -- Linux loves allowing you to do your own keybinds, but macOS (and Windows, when I get to it) absolutely do not.
-   Several places where I had to guard against imports that don't exist on non-mac systems
-   SO many weird specific Mac-specific things for making sure the window worked and behaved as expected. Mildly cursed code, honestly.

## Added

-   Global Hotkey Support
    -   **Linux**:
        -   The Linux approach uses an approach based on [Waybind](https://github.com/postman721/Waybind).
        -   It should be compatible with X11, Wayland, and WM/DE.
        -   I use Wayland and Niri and these new changes worked very well.
        -   Triggered with <kbd>super</kbd> + <kbd>shift</kbd> + <kbd>\\</kbd>\|
    -   **macOS**:
        -   Uses [QuickMacHotKey](https://github.com/glyph/QuickMacHotKey)
        -   Triggered with <kbd>cmd</kbd> + <kbd>shift</kbd> + <kbd>\\</kbd>
    -   For now, the hotkey is still hard-coded but the next update will add in configurability for this and many other UI and behavioral components!

## Changed

-   Moved to a single, persistent background application which is reveal
-   Rewrote Linux install to use `systemctl --user` if available, spins up in the background and warns you if not
-   Rewrote all build scripts to use `cd -a` to avoid broken symlinks
-   Likewise, build scripts now use `tar.gz` files for artifacts to maintain symlinks.
-   Rewrote install scripts to use `cd -a` and include macOS build flows
    -   The macOS build flow automatically grabs `pinentry-mac` from homebrew if it's not installed
    -   automatically configures it as pinentry for `rbw`
    -   adds `rbw-quick-access` to your login item if you permit it
    -   starts `rbw-quick-access` in the background

## Fixed

-   Sometimes inputs like the up or down arrows to get into/out of the results/input field wouldn't work, or would work inconsistently
-   Fixed a bug where opening up quick-access wouldn't start with the text input field active and text fully highlighted by default.
-   Fixed a platform-specific conflict with the key handlers fighting between the main window and its children. In short, pressing `esc`, `up` or `down` wasn't working on macOS while working fine on Linux.
-   Install scripts not removing old installations
-   Install scripts not stopping the old, potentially active installation before removing it
