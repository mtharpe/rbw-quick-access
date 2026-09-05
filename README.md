# RBW Quick Access

This is a tool that aims to replicate 1Password's Quick-Access overlay with a Bitwarden (using `rbw`) backed equivalent.

## Behaviors to Replicate:

### Fields

We should be able to see the following for each entry, as well as search by:

- Entry Name
- Website
- Username

### Keyboard Shortcuts

**For all of these, the window is dismissed**

- `enter` opens the URL, if there is one.
- `alt + enter` does the same? I'm not sure why...
- `ctrl + c` copies the username (if present)
- `ctrl + shift + c` copies the password
- `ctrl + alt + c` copies the TOTP
- `ctrl + o` - NOOP; this opens the item in a new window. I don't want to deal with integrating with the BitWarden GUI too...
- `ctrl + shift + o` - also NOOP; this opens the item in the full 1Password window, not just the viewer window, and that's just not gonna happen...

## Dependencies

- Python 3.10
- `rbw`
