# RBW Quick Access

This is a tool that aims to replicate 1Password's Quick-Access overlay backed by [`rbw`](https://github.com/doy/rbw).

# Demo

![](https://stuff.forgeserv.cloud/Jose's%20Stuff/Screenshots/2026-09-05_09%3A01%3A32PM.mp4)

# Design Goals

## Quick Startup

## Large Dataset Support

Using PyQT6's delegate, events, and sticking with primitives where possible, the password list is able to easily handle hundreds of thousands of secrets from your vault just like that! 🫰

## Parity with 1Password

When designing this, I was moving from 1Password after using it for 8+ years straight. Moving to [Vault|Bit]warden was mostly a breeze, but this was the one and only working flow that was broken up entirely.

### Fields

To succeed in replicating the feel (and more importantly, functionality) of the 1Password quick-access app(let?). The biggest things were being able to search by, and see, the following when browsing and searching:

- Entry Name
- Website
- Username

### Keyboard Shortcuts

After 8 years with this system, the keyboard shortcuts were pretty well engrained in my head

- `enter` opens the URL, if there is one.
- ~~`alt + enter` does the same? I'm not sure why...~~ since this was redundant, I didn't bother
- `ctrl + c` copies the username (if present)
- `ctrl + shift + c` copies the password
- `ctrl + alt + c` copies the TOTP
- `ctrl + o` - NOOP; this opens the item in a new window. I don't want to deal with integrating with the BitWarden GUI too...
- `ctrl + shift + o` - also NOOP; this opens the item in the full 1Password window, not just the viewer window, and that's just not gonna happen...

## Dependencies

- Python 3.10
- `rbw` fully configured and logged in
  - if `rbw ** --clipboard` doesn't work for you, then neither will this :(

# Milestones:

- The next big milestone is to re-architect the app such that it stays alive between launches, such that running `rbw-quick-access --show` (or something to that effect) will spin up a singleton if it isn't running, and shows it. This would mean a single binary file is all I'd need to distribute and would make installation easier.
- Eventually we'll want a configuration screen which:
  - Would allow you to select a vault
  - ..or a specific folder
  - Change sorting methods (like sorting by most-used)
  - Change the in-app keyboard shortcuts
