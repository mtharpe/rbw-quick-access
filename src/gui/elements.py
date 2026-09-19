"""
@author Jose Stovall | oitsjustjose

Various GUI elements used by other widgets throughout the application
"""

from collections.abc import Callable
from threading import Thread
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QFontInfo, QFontMetrics, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

import rbw
from config import Keybind, get_config
from rbw import BitwardenEntry

if TYPE_CHECKING:
    from gui import MainWindow


class DynamicStackedWidget(QStackedWidget):
    def sizeHint(self) -> QSize:
        """Overrides the sizeHint to grab it from the current element if set

        Returns:
            QSize: The size hint from the currently active widget
        """
        current = self.currentWidget()
        if not current:
            return super().sizeHint()
        return current.sizeHint()

    def minimumSizeHint(self) -> QSize:
        """Overrides the _minimum_ sizeHint to grab it from the current element if set

        Returns:
            QSize: The  _minimum_ size hint from the currently active widget
        """
        current = self.currentWidget()
        if not current:
            return super().minimumSizeHint()
        return current.minimumSizeHint()


class SearchBox(QLineEdit):
    results_ready = pyqtSignal(tuple)

    def __init__(self, parent: "MainWindow"):
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

        # Handlers for hiding and moving into/out of the search box
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Down, Qt.Key.Key_Up):
            a0.ignore()
            return

        # Settings window handler
        if a0.modifiers() == Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_Comma:
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

    def __init__(self, parent: "MainWindow"):
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
        self.config = get_config()
        layout = QHBoxLayout()
        layout.addWidget(self.__make_guide(self.config.copy_username.to_string(qt_fmt=True), "Copy username"))
        layout.addWidget(self.__make_guide(self.config.copy_password.to_string(qt_fmt=True), "Copy password"))
        layout.addWidget(self.__make_guide(self.config.copy_totp.to_string(qt_fmt=True), "Copy totp"))
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


class KeybindEditor(QKeySequenceEdit):
    def __init__(self, parent: QWidget, keybind: Keybind, on_change: Callable[[QKeySequence, Keybind], None]):
        """A super simple QWidget wrapper around a QKeySequenceEditor, which
        adds a label, sets defaults on the KeySequenceEdit, and binds on_change

        Args:
            parent (QWidget): The parent to this widget
            keybind (Keybind): The current keybind to read/set
            on_change (Callable[[QKeySequence, Keybind], None]): The callback which provides
              the keyseq and affected keybind when the keysequence is changed
        """
        super().__init__(keybind.to_string(qt_fmt=True), parent)
        self.__on_change = on_change
        self.__keybind = keybind
        self.__keybind.on_restored.connect(self.__on_restored)

        # Debounce timer for the sequence change evt
        self.__pending_seq: QKeySequence | None = None
        self.__change_timer = QTimer(self)
        self.__change_timer.setSingleShot(True)
        self.__change_timer.timeout.connect(self.__commit_changed_keybind)

        self.setClearButtonEnabled(True)
        self.setMaximumSequenceLength(1)
        self.keySequenceChanged.connect(self.__on_change_internal)

    def __on_change_internal(self, sequence: QKeySequence):
        """An internal change handler to help debounce events"""
        if self.__pending_seq:
            return
        self.__pending_seq = sequence
        self.__change_timer.start(50)

    def __commit_changed_keybind(self):
        """The actual handler for changed keybinds, debounced"""
        if not self.__pending_seq:
            return

        self.__on_change(self.__pending_seq, self.__keybind)
        self.__pending_seq = None
        self.clearFocus()

    def __on_restored(self):
        """Unsets whatever changes were made to this keybind"""
        self.setKeySequence(QKeySequence.fromString(self.__keybind.to_string(qt_fmt=True), format=QKeySequence.SequenceFormat.PortableText))


class DismissableDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, msg: str):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)

        msg_lbl = QLabel(msg)
        layout = QVBoxLayout()
        layout.addWidget(msg_lbl)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class YesNoDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, msg: str):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        msg_lbl = QLabel(msg)
        layout = QVBoxLayout()
        layout.addWidget(msg_lbl)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
