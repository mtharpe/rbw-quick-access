import webbrowser
from threading import Thread
from typing import cast

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QFontInfo, QFontMetrics, QHideEvent, QKeyEvent, QShowEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

import rbw
from config import Config
from plat import IS_MAC, get_platform_handler
from rbw import BitwardenEntry


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__last_result_id = -1
        self.__selection: BitwardenEntry | None = None
        self.__platform_handler = get_platform_handler(self)
        self.__platform_handler.on_show_signal.connect(self.show)
        self.__config = Config.load()
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


class SearchBox(QLineEdit):
    results_ready = pyqtSignal(tuple)

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.results_ready.connect(parent.on_results_ready)
        self.__request_id = 0

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(640)
        self.setFixedHeight(72)
        self.textChanged.connect(self.on_input_changed)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Overrides the ↑, ↓ and escape inputs so that the main window can handle it on its own"""
        if not a0:
            return

        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Down, Qt.Key.Key_Up):
            a0.ignore()
            return

        super().keyPressEvent(a0)

    def on_input_changed(self, inp: str):
        """Called when the text input is changed, spinning up a new thread to do the `rbw` query and update the results.

        Args:
            inp (str): the search query
        """
        self.__request_id += 1
        Thread(target=self.__search, args=[inp, self.__request_id]).start()

    def __search(self, inp: str, request_id: int):
        """A function just for the purpose of doing the search and notifying the parent of the new results

        Args:
            inp (str): the search query
        """
        results = rbw.search(inp)
        self.results_ready.emit((request_id, results))


class SearchResults(QListWidget):
    sel_changed = pyqtSignal(object)

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.setItemDelegate(SearchResultDelegate(self))
        self.horizontalScrollBar().hide()  # type: ignore -- this is always gonna be here, right?
        self.__results: list[SearchResult] = []
        self.itemSelectionChanged.connect(self.selection_changed)
        self.sel_changed.connect(parent.on_selection_changed)

    def update_entries(self, results: list[BitwardenEntry]):
        self.clear()
        self.__results = [SearchResult(x) for x in results]
        for w in self.__results:
            self.addItem(w)

    def selection_changed(self):
        items = cast(list[SearchResult], self.selectedItems())
        # `items` will be EMPTY when `self.clearSelection()` is called,
        #   hence the check and ternary.
        # Also, we won't have (or don't care about) more than 1 entry
        self.sel_changed.emit(items[0].bw_data if items else None)

    def try_focus(self):
        """Attempts to take focus *if* there are any valid search results"""
        if not len(self.__results):
            return

        self.setFocus()
        self.setCurrentRow(0)
        self.__results[0].setSelected(True)

    def unfocus(self):
        # Allow only if we're at the top of the results (or have none)
        if self.__results and self.currentRow() != 0:
            return False

        self.clearFocus()
        self.clearSelection()
        return True


class SearchResultDelegate(QStyledItemDelegate):
    VERTICAL_PADDING = 10

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)

        return QSize(
            size.width(),
            size.height() + self.VERTICAL_PADDING * 2,
        )

    def paint(self, painter, option, index):
        if not painter:
            return

        # REGION rebuild standard QListWidgetItem painting
        painter.save()

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""  # Unset the text now, so the normal render method doesn't try to render it.

        widget = opt.widget
        style = widget.style() if widget else QApplication.style()
        if not style:
            return
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        # ENDREGION rebuild standard QListWidgetItem painting

        rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, widget)
        color: QColor
        # Nasty coloring block since this is kinda... weird. Doesn't take on QSS theme like it should
        #  And yes, the bitwise and is necessary T_T
        if opt.state & QStyle.StateFlag.State_Selected:
            color = QColor("#16161e")
        else:
            color = opt.palette.color(opt.palette.ColorRole.Text)
        painter.setPen(color)

        item: BitwardenEntry = index.data(Qt.ItemDataRole.UserRole)

        bold_font = QFont(opt.font)
        bold_font.setBold(True)

        painter.setFont(bold_font)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignVCenter,
            item.name,
        )

        # Measure where the bold portion ended
        x = rect.x() + QFontMetrics(bold_font).horizontalAdvance(item.name)

        normal_font = opt.font
        painter.setFont(normal_font)
        painter.drawText(
            rect.adjusted(x - rect.x(), 0, 0, 0),
            Qt.AlignmentFlag.AlignVCenter,
            f"  -  {item.user or '—'}  -  {item.uri}",
        )

        painter.restore()


class SearchResult(QListWidgetItem):
    def __init__(self, bw_data: BitwardenEntry):
        super().__init__()
        self.bw_data = bw_data
        # Store the data for use in the delegate :)
        self.setData(Qt.ItemDataRole.UserRole, bw_data)


class HotkeyGuide(QWidget):
    def __init__(self):
        super().__init__()

        ctrl = "Cmd" if IS_MAC else "Ctrl"
        alt = "Opt" if IS_MAC else "Alt"

        layout = QHBoxLayout()
        layout.addWidget(self.__make_guide(f"{ctrl}+C", "Copy username"))
        layout.addWidget(self.__make_guide(f"{ctrl}+Shift+C", "Copy password"))
        layout.addWidget(self.__make_guide(f"{alt}+Shift+C", "Copy totp"))
        self.setLayout(layout)

    def __make_guide(self, keybind: str, text: str) -> QWidget:
        family = QFontInfo(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)).family()

        lbl = QLabel()
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setText(f"""
            <span style="
                font-family: {family};
                background-color: #9aa5ce;
                color: #16161e;
            ">
                {keybind}
            </span>
        &nbsp; {text}
        """)
        return lbl


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.label = QLabel("Settings :)")
        layout.addWidget(self.label)
        self.setLayout(layout)
