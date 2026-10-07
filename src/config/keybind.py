"""
@author Jose Stovall | oitsjustjose

A simple wrapper for the keybind mechanism used by QT and evdev/macOS
"""

from pydantic import BaseModel
from PyQt6.QtCore import QKeyCombination
from PyQt6.QtGui import QKeySequence

from plat import IS_MAC


class Keybind(BaseModel):
    """Defines a given trigger key and modifiers"""

    trigger: str
    ctrl: bool
    alt: bool
    meta: bool
    shift: bool

    # Use a private attribute for UI-only state so it doesn't
    # leak into the JSON during model_dump()
    _uncommitted = None

    # def __init__(self, trigger: str, ctrl: bool = False, alt: bool = False, meta: bool = False, shift: bool = False):
    #     super().__init__()
    #     self.trigger = trigger
    #     self.ctrl = ctrl
    #     self.alt = alt
    #     self.meta = meta
    #     self.shift = shift

    #     # The uncommitted, changed keybind, so it can be restored later
    #     self.uncommitted: Keybind | None = None

    @staticmethod
    def deserialize(text_repr: str) -> "Keybind":
        """Converts a text-based shortcut (like "Ctrl+A") into
        a proper Keybind entry

        Args:
            text_repr (str): The text representation, as obtained by ::to_text

        Returns:
            Keybind: The built keybind
        """
        parts = text_repr.lower().split("+")

        ctrl = "ctrl" in parts
        alt = "alt" in parts
        meta = "meta" in parts
        shift = "shift" in parts
        trigger = parts[-1]

        return Keybind(
            trigger=trigger,
            ctrl=ctrl,
            alt=alt,
            meta=meta,
            shift=shift,
        )

    def serialize(self, qt_fmt=False) -> str:
        """Creates a (QT-compatible if set) string from this keybind"""
        ctrl = self.meta if (qt_fmt and IS_MAC) else self.ctrl
        meta = self.ctrl if (qt_fmt and IS_MAC) else self.meta

        return "+".join(
            filter(
                bool,
                [
                    "Ctrl" if ctrl else "",
                    "Alt" if self.alt else "",
                    "Meta" if meta else "",
                    "Shift" if self.shift else "",
                    self.trigger,
                ],
            )
        )

    def display(self) -> str:
        """Returns a user-facing representation of the keybind."""
        if IS_MAC:
            parts = []

            if self.ctrl:
                parts.append("⌃")

            if self.alt:
                parts.append("⌥")

            if self.meta:
                parts.append("⌘")

            if self.shift:
                parts.append("⇧")

            trigger = self.trigger.upper()

            if trigger == "ENTER":
                trigger = "↩"
            elif trigger == "SPACE":
                trigger = "Space"
            elif trigger == "ESCAPE":
                trigger = "Esc"

            parts.append(trigger)

            return "".join(parts)

        return self.serialize()

    def qt_matches(self, combo: QKeyCombination) -> bool:
        """Determines if a given key combination matches this keybind

        Args:
            combo (QKeyCombination): The QT Key Combination coming in

        Returns:
            bool: True if the key combo is an exact match
        """
        # Why reinvent the wheel - self.to_string uses the nicely defined creator below
        self_seq = QKeySequence.fromString(self.serialize(qt_fmt=True), QKeySequence.SequenceFormat.PortableText)
        return self_seq.matches(QKeySequence(combo)) == QKeySequence.SequenceMatch.ExactMatch

    def set(self, new_sequence: QKeySequence):
        """Called when changed by the QT GUI

        Args:
            new_sequence (QKeySequence): The new keybind sequence
        """
        # The QT key format here is.... weird. This was easiest.
        as_str = new_sequence.toString(QKeySequence.SequenceFormat.PortableText)
        self._uncommitted = Keybind.deserialize(as_str)

    def commit(self):
        """Commits the uncommitted changes to the instance"""
        if not self._uncommitted:
            return

        # macOS compatability kinda sucks. Oh well.
        self.ctrl = self._uncommitted.meta if IS_MAC else self._uncommitted.ctrl
        self.meta = self._uncommitted.ctrl if IS_MAC else self._uncommitted.meta

        self.trigger = self._uncommitted.trigger
        self.alt = self._uncommitted.alt
        self.shift = self._uncommitted.shift

        self._uncommitted = None

    def reset(self):
        """Just a wrapper, since _uncommitted is technically 'hidden'"""
        self._uncommitted = None

    def __str__(self) -> str:
        return self.serialize()
