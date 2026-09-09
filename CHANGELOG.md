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

## Changed

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
