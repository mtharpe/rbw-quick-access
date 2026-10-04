"""
@author Jose Stovall | oitsjustjose

The core GUI elements for the application
"""

import webbrowser
from datetime import datetime as dt
from datetime import timezone
from time import sleep

from PyQt6.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QHideEvent, QKeyEvent, QKeySequence, QWindow
from PyQt6.QtWidgets import QCheckBox, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

import rbw
from config import Config, Keybind
from gui.elements import DismissableDialog, DynamicStackedWidget, HotkeyGuide, KeybindEditor, SearchBox, SearchResults, YesNoDialog
from plat import IS_LINUX, get_platform_handler
from rbw import BitwardenEntry


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__last_result_id = -1
        self.__selection: BitwardenEntry | None = None
        self.__config = Config.get()
        self.__settings_open = False
        self.__hidden_at = dt.fromtimestamp(0, tz=timezone.utc)

        self.plat_handler = get_platform_handler(self)
        self.plat_handler.on_show_signal.connect(self.show_and_activate)

        # Dependent widgets for this class
        self.search_widget = SearchBox(self)
        self.results_widget = SearchResults(self)
        self.hotkey_guide = HotkeyGuide()

        """REGION VIEW CONFIGURATIONS"""

        self.qa_view = QWidget()
        qa_layout = QVBoxLayout()
        qa_layout.addWidget(self.search_widget)
        qa_layout.addWidget(self.results_widget)
        qa_layout.addWidget(self.hotkey_guide)
        self.qa_view.setLayout(qa_layout)

        self.settings_view = SettingsWidget(self)

        self.views = DynamicStackedWidget()
        self.views.addWidget(self.qa_view)
        self.views.addWidget(self.settings_view)

        """ENDREGION VIEW CONFIGURATIONS"""

        self.search_widget.on_input_changed("")
        self.setCentralWidget(self.views)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(self.width(), qa_layout.sizeHint().height())
        # Wait to configure the window until other QT configuration has been completed
        self.plat_handler.configure_window()

    def on_focus_window_changed(self, window: QWindow | None):
        """Called when the focused application has been changed

        Args:
            window (QWindow | None): The window we have changed to
        """
        if window is not self.windowHandle():
            self.hide()

    def show_and_activate(self) -> None:
        """Shows the window and pushes it to the front"""
        if not self.isVisible():
            self.show()

        if self.__settings_open:
            self.toggle_settings()

        # Perform the platform-specific activation **first**
        self.plat_handler.on_show()
        self.block_until_unlock()

        # If it's been more than 30 seconds since you hid the window,
        #  set up the state to start typing fresh again
        if (dt.now(tz=timezone.utc) - self.__hidden_at).seconds >= 30:
            self.results_widget.unfocus()
            self.search_widget.setFocus()
            self.search_widget.selectAll()

        self.raise_()
        self.activateWindow()

    def toggle_settings(self) -> None:
        """Shows (or hides) the settings widget"""
        new_view: QWidget
        if self.__settings_open:
            new_view = self.qa_view
        else:
            new_view = self.settings_view

        self.__settings_open = not self.__settings_open
        self.views.setCurrentWidget(new_view)
        # Short delay before adjusting size for consistent behavior
        QTimer.singleShot(0, self.adjustSize)

    def hideEvent(self, a0: QHideEvent | None) -> None:
        """Called when the QWidget is hidden. In this case, it's only used
        to call the platform handler's on_hide function if relevant.

        Args:
            a0 (QShowEvent | None): The event in (unused - passed to super)
        """
        self.__hidden_at = dt.now(tz=timezone.utc)
        self.plat_handler.on_hide()
        rbw.sync()
        return super().hideEvent(a0)

    def changeEvent(self, a0: QEvent | None) -> None:
        """Called when the QWidget focus is changed. In our case we use it
        to ensure that we hide the window when it's lost focus.

        Args:
            a0 (QEvent | None): The event in
        """

        if a0 and a0.type() == QEvent.Type.WindowDeactivate:
            print("Hi")

        return super().changeEvent(a0)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Overrides the generalized keyPressEvent to handle it ourselves after super() is called
        Used to handle non-ASCII inputs like Esc/Up/Down

        Args:
            a0 (QKeyEvent | None): The keypress event, if valid
        """
        if not a0:
            return

        def __do_app_input() -> bool:
            """Handles application wide inputs like quitting on ESC, moving focus from search & result widgets

            Returns:
                bool: True if an action was taken (consuming the input), false otherwise
            """

            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_Comma:
                self.toggle_settings()
                return True

            if a0.key() == Qt.Key.Key_Escape:
                self.hide()
                return True

            if a0.key() == Qt.Key.Key_Down and not self.results_widget.hasFocus():
                self.results_widget.try_focus()
                return True

            if a0.key() == Qt.Key.Key_Up and self.results_widget.unfocus():
                self.search_widget.setFocus()
                return True

            return False

        def __do_selection_input(sel: BitwardenEntry) -> bool:
            """Handls selection-specific inputs like opening, copying, etc..

            Args:
                sel (BitwardenEntry): The validated, non-null bitwarden data entry

            Returns:
                bool: True if an action was taken (consuming the input), false otherwise
            """

            if self.__config.open_in_browser.qt_matches(a0.keyCombination()):
                if sel.uri:
                    webbrowser.open(sel.uri)
                self.hide()
                return True

            if self.__config.copy_username.qt_matches(a0.keyCombination()):
                if sel.user:
                    rbw.copy_username(sel)
                self.hide()
                return True

            if self.__config.copy_password.qt_matches(a0.keyCombination()):
                rbw.copy_password(sel)
                self.hide()
                return True

            if self.__config.copy_totp.qt_matches(a0.keyCombination()):
                rbw.copy_totp(sel)
                self.hide()
                return True

            return False

        if __do_app_input():
            return a0.accept()
        if self.__selection and __do_selection_input(self.__selection):
            return a0.accept()
        # Only call super when we didn't do something special
        super().keyPressEvent(a0)

    def on_results_ready(self, data: tuple[int, list[BitwardenEntry] | None]):
        """Takes the new search results and updates the results widget

        Args:
            new_results (list[BitwardenEntry]): _description_
        """

        request_id, results = data
        if request_id <= self.__last_result_id:
            return

        self.__last_result_id = request_id
        self.results_widget.update_entries(results or [])

    def on_selection_changed(self, selection: BitwardenEntry | None):
        """Delegate used by the emitter in the selection widget to update the current
        selection, this way when we type a keyboard shortcut we know what to activate
        it on (if any)

        Args:
            selection (BitwardenEntry | None): The selection made - None if we went back to search
        """
        self.__selection = selection

    def block_until_unlock(self):
        """
        Blocks the main thread until RBW has been unlocked

        This is done to prevent each typed character from triggering
            a new unlock, thus triggering a new pinentry window to
            spawn for each character input while not unlocked.
        """
        while not rbw.unlock():
            sleep(0.1)


class SettingsWidget(QWidget):
    cancel_pressed = pyqtSignal()

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.main_window = parent
        self.__config = Config.get()

        custom_font = QFont()
        custom_font.setPixelSize(24)
        self.label = QLabel("Settings")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(custom_font)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label)

        """REGION: Keybind Grid"""
        keybind_grid = QGridLayout()
        # Go through each label and KeybindChanger and configure it into an evenly spaced grid
        for row, (label, editor) in enumerate(
            [
                ("Show Window", KeybindEditor(self, self.__config.show, self.on_show_key_changed, self.cancel_pressed)),
                ("Open Item in Browser", KeybindEditor(self, self.__config.open_in_browser, self.on_key_changed, self.cancel_pressed)),
                ("Copy Username", KeybindEditor(self, self.__config.copy_username, self.on_key_changed, self.cancel_pressed)),
                ("Copy Password", KeybindEditor(self, self.__config.copy_password, self.on_key_changed, self.cancel_pressed)),
                ("Copy TOTP", KeybindEditor(self, self.__config.copy_totp, self.on_key_changed, self.cancel_pressed)),
            ]
        ):
            keybind_grid.addWidget(QLabel(label), row, 0)
            keybind_grid.addWidget(editor, row, 1)
        # Give both columns equal stretch
        keybind_grid.setColumnStretch(0, 1)
        keybind_grid.setColumnStretch(1, 1)
        """ENDREGION: Keybind Grid"""

        """REGION: Checkboxes"""
        # I guess we'll eval this each time anyways? ¯\_(ツ)_/¯
        open_at_startup_layout = QHBoxLayout()
        self.__open_at_startup_chkbx = QCheckBox()
        self.__open_at_startup_chkbx.setChecked(self.__config.open_at_startup)
        self.__open_at_startup_chkbx.checkStateChanged.connect(self.on_open_at_startup_changed)
        open_at_startup_layout.addWidget(QLabel("Open at Startup"))
        open_at_startup_layout.addWidget(self.__open_at_startup_chkbx)
        """ENDREGION: Checkboxes"""

        """REGION: Buttons"""
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save_pressed)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.on_cancel_pressed)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        """ENDREGION: Buttons"""

        layout.addLayout(keybind_grid)
        not IS_LINUX and layout.addLayout(open_at_startup_layout)  # type: ignore
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.adjustSize()
        # Keeps the first KeybindChanger from stealing focus on open
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def on_show_key_changed(self, seq: QKeySequence, kb: Keybind):
        """Called whenever the show key has been changed"""
        key = seq.toString(QKeySequence.SequenceFormat.PortableText).split("+")[-1]
        valid = self.main_window.plat_handler.validate(key)
        if not valid:
            dlg = DismissableDialog(self, "Failed to Set Key", f"Key '{key}' is not a valid choice on your OS. Please pick another!")
            dlg.exec()
            return

        self.on_key_changed(seq, kb)

    def on_key_changed(self, seq: QKeySequence, kb: Keybind):
        """Called when any other key has been changed"""
        kb.set(seq)
        self.setFocus()

    def on_open_at_startup_changed(self, new_state: Qt.CheckState):
        """Called when the checkbox for "Open at Startup" is changed"""
        self.__open_at_startup_tmp = new_state != Qt.CheckState.Unchecked

    def on_save_pressed(self):
        """Called when the Save button has been pressed"""
        # Handle the temporary, stored startup button state.
        if self.__open_at_startup_tmp != self.__config.open_at_startup:
            self.__config.open_at_startup = self.__open_at_startup_tmp
            del self.__open_at_startup_tmp
            self.main_window.plat_handler.configure_startup(self.__config.open_at_startup)

        self.__config.save()

        dlg = YesNoDialog(self, "Restart?", "Saving requires an application restart. Restart now?")
        if dlg.exec():
            self.main_window.plat_handler.restart_app()

    def on_cancel_pressed(self):
        """Called when the cancel button has been pressed -- resets all changes"""
        # KeybindEditor will unset the uncommitted change since it listens to self.cancel_pressed
        self.cancel_pressed.emit()
        # Also want to undo any modifications to the checkbox here.
        self.__open_at_startup_chkbx.setChecked(self.__config.open_at_startup)
        self.main_window.toggle_settings()
