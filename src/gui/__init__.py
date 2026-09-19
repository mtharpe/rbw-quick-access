"""
@author Jose Stovall | oitsjustjose

The core GUI elements for the application
"""

import webbrowser

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QHideEvent, QKeyEvent, QShowEvent
from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

import rbw
from config import get_config
from gui.elements import HotkeyGuide, KeybindChanger, SearchBox, SearchResults
from plat import get_platform_handler
from rbw import BitwardenEntry


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__last_result_id = -1
        self.__selection: BitwardenEntry | None = None
        self.__platform_handler = get_platform_handler(self)
        self.__platform_handler.on_show_signal.connect(self.show)
        self.__config = get_config()
        self.__settings_open = False

        self.search_widget = SearchBox(self)
        self.results_widget = SearchResults(self)
        self.hotkey_guide = HotkeyGuide()

        self.settings_widget = SettingsWidget(self)
        self.settings_widget.config_changed.connect(self.__update_config)

        # The widgets above aren't using this window as the parent
        #  Plus we want them in the box layout, so...
        layout = QVBoxLayout()
        layout.addWidget(self.search_widget)
        layout.addWidget(self.results_widget)
        layout.addWidget(self.hotkey_guide)
        layout.addWidget(self.settings_widget)

        # On top of that, you can't set a layout on a QMainWindow.
        #  So this is the route around that. Not bad
        layout_widget = QWidget()
        layout_widget.setLayout(layout)
        layout_widget.adjustSize()
        self.search_widget.on_input_changed("")
        self.setCentralWidget(layout_widget)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

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
        self.__platform_handler.on_show()

    def toggle_settings(self) -> None:
        """Shows (or hides) the settings widget"""
        if self.__settings_open:
            self.settings_widget.hide()
            self.search_widget.show()
            self.results_widget.show()
            self.hotkey_guide.show()
        else:
            self.settings_widget.show()
            self.search_widget.hide()
            self.results_widget.hide()
            self.hotkey_guide.hide()

        self.__settings_open = not self.__settings_open
        # Do a short delay before readjusting the main window size
        QTimer.singleShot(0, self.adjustSize)

    def hideEvent(self, a0: QHideEvent | None) -> None:
        """Called when the QWidget is hidden. In this case, it's only used
        to call the platform handler's on_hide function if relevant.

        Args:a
            a0 (QShowEvent | None): The event in (unused - passed to super)
        """
        self.__platform_handler.on_hide()
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

    def __update_config(self):
        """Called when the config has been updated"""
        print("Config update signal received!")
        self.__config = get_config()


class SettingsWidget(QWidget):
    config_changed = pyqtSignal()

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.__config = get_config()

        self.label = QLabel("Settings")
        custom_font = QFont()
        custom_font.setPixelSize(24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(custom_font)
        self.btn = QPushButton("Back")
        self.btn.clicked.connect(parent.toggle_settings)

        self.editors = [
            KeybindChanger(self, "Show Window", self.__config.show, self.config_changed.emit),
            KeybindChanger(self, "Open Item in Browser", self.__config.open_in_browser, self.config_changed.emit),
            KeybindChanger(self, "Copy Username", self.__config.copy_username, self.config_changed.emit),
            KeybindChanger(self, "Copy Password", self.__config.copy_password, self.config_changed.emit),
            KeybindChanger(self, "Copy TOTP", self.__config.copy_totp, self.config_changed.emit),
        ]

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label)
        [layout.addWidget(w) for w in self.editors]
        layout.addWidget(self.btn)

        self.setLayout(layout)
        # Keeps the first KeybindChanger from stealing focus on open
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()
