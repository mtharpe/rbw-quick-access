import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QHideEvent, QKeyEvent, QShowEvent
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

        self.settings_widget = SettingsWidget(self)

        # The widgets above aren't using this window as the parent
        #  Plus we want them in the box layout, so...
        layout = QVBoxLayout()
        layout.addWidget(self.search_widget)
        layout.addWidget(self.results_widget)
        layout.addWidget(HotkeyGuide())

        # On top of that, you can't set a layout on a QMainWindow.
        #  So this is the route around that. Not bad
        layout_widget = QWidget()
        layout_widget.setLayout(layout)
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
        else:
            self.settings_widget.show()
        self.__settings_open = not self.__settings_open

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


class SettingsWidget(QMainWindow):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.__config = get_config()

        self.main_window = parent
        self.label = QLabel("Settings :)")
        self.editors = [
            KeybindChanger(self, "Copy Username", self.__config.copy_username),
        ]

        self.btn = QPushButton("Back")
        self.btn.clicked.connect(self.hide)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn)
        [layout.addWidget(w) for w in self.editors]

        layout_widget = QWidget()
        layout_widget.setLayout(layout)
        # self.setFixedSize(layout_widget.sizeHint())
        self.setCentralWidget(layout_widget)

    def show(self):
        super().show()

        self.main_window.hide()
        self.main_window.clearFocus()
        self.setFocus()
        self.raise_()

    def hide(self):
        super().hide()

        self.clearFocus()
        self.main_window.show()
        self.main_window.setFocus()
        self.main_window.raise_()
