# 0.0.3

## macOS Port

WOOF - this was a rough one. I ran into so many challenges along the way:

- Didn't have a Mac to do builds on
  - Especially not one with a new enough processor for QT6. My newest one is a 2014 MBP
- `rbw` build was drastically slow on macOS - had to compile my own build from a combination of two different changes (see rbw/README.md). JUST for macOS -- Linux works amazingly
- Had to fully re-do the build scripts and install scripts for both Linux and macOS to support/ignore the various macOS-specific flags and steps
- Global keybind implementation was necessary to get this to work -- Linux loves allowing you to do your own keybinds, but macOS (and Windows, when I get to it) absolutely do not.
- Several places where I had to guard against imports that don't exist on non-mac systems
- SO many weird specific Mac-specific things for making sure the window worked and behaved as expected. Mildly cursed code, honestly.