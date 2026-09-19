"""
@author Jose Stovall | oitsjustjose

The core GUI elements for the application
"""

import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QHideEvent, QKeyEvent, QKeySequence, QShowEvent
from PyQt6.QtWidgets import QDialog, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

import rbw
from config import Keybind, get_config
from gui.elements import DynamicStackedWidget, HotkeyGuide, KeybindChanger, SearchBox, SearchResults
from plat import get_platform_handler
from rbw import BitwardenEntry


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__last_result_id = -1
        self.__selection: BitwardenEntry | None = None
        self.__config = get_config()
        self.__settings_open = False

        self.plat_handler = get_platform_handler(self)
        self.plat_handler.on_show_signal.connect(self.show)

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

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Called when the QWidget is shown. In this case, it's used to pre-propagate
        the search results with the results from an empty string search

        Args:a
            a0 (QShowEvent | None): The event in (unused - passed to super)
        """
        super().showEvent(a0)

        self.raise_()
        self.activateWindow()
        self.results_widget.unfocus()
        self.search_widget.setFocus()
        self.search_widget.selectAll()
        self.plat_handler.on_show()

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

        Args:a
            a0 (QShowEvent | None): The event in (unused - passed to super)
        """
        self.plat_handler.on_hide()
        return super().hideEvent(a0)

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

            if a0.modifiers() == Qt.KeyboardModifier.MetaModifier and a0.key() == Qt.Key.Key_Comma:
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


class SettingsWidget(QWidget):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.main_window = parent
        self.__config = get_config()

        custom_font = QFont()
        custom_font.setPixelSize(24)
        self.label = QLabel("Settings")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(custom_font)

        self.btn = QPushButton("Save")
        self.btn.clicked.connect(self.on_save_pressed)

        self.editors = [
            KeybindChanger(self, "Show Window", self.__config.show, self.on_show_changed),
            KeybindChanger(self, "Open Item in Browser", self.__config.open_in_browser, self.on_key_changed),
            KeybindChanger(self, "Copy Username", self.__config.copy_username, self.on_key_changed),
            KeybindChanger(self, "Copy Password", self.__config.copy_password, self.on_key_changed),
            KeybindChanger(self, "Copy TOTP", self.__config.copy_totp, self.on_key_changed),
        ]

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label)
        [layout.addWidget(w) for w in self.editors]
        layout.addWidget(self.btn)

        self.setLayout(layout)
        self.adjustSize()
        # Keeps the first KeybindChanger from stealing focus on open
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

    def on_show_changed(self, seq: QKeySequence, kb: Keybind):
        """Called whenever the show key has been changed"""
        # TODO: Make the PlatformHandler class validate the keybind
        valid = self.main_window.plat_handler.validate(seq)
        if not valid:
            # TODO: Visual Popup or propagate on keybind?
            return

        self.on_key_changed(seq, kb)

    def on_key_changed(self, seq: QKeySequence, kb: Keybind):
        """Called when any other key has been changed"""
        kb.set(seq)

    def on_save_pressed(self):
        """Called when the Save button has been pressed"""
        # self.main_window.toggle_settings()
        # TODO: Popup Window

        dlg = QDialog(self)
        dlg.setWindowTitle("Restart?")
        dlg.exec()

        self.__config.save()
