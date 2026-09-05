from threading import Thread
from typing import cast

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QShowEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from rbw import BitwardenEntry, search


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.__app = app
        self.__last_result_id = -1
        self.search_widget = SearchBox(self)
        self.results_widget = SearchResults(self)

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
        self.setCentralWidget(layout_widget)

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Called when the QWidget is shown. In this case, it's used to pre-propagate
        the search results with the results from an empty string search

        Args:
            a0 (QShowEvent | None): The event in (unused - passed to super)
        """
        super().showEvent(a0)
        self.search_widget.on_input_changed("")

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Overrides the generalized keyPressEvent to handle it ourselves after super() is called
        Used to handle non-ASCII inputs like Esc/Up/Down

        Args:
            a0 (QKeyEvent | None): The keypress event, if valid
        """
        super().keyPressEvent(a0)
        if a0 and a0.key() == Qt.Key.Key_Escape:
            return self.__app.quit()

        if a0 and a0.key() == Qt.Key.Key_Down and not self.results_widget.hasFocus():
            self.results_widget.try_focus()

        if a0 and a0.key() == Qt.Key.Key_Up and self.results_widget.unfocus():
            self.search_widget.setFocus()

    def on_results_ready(self, data: tuple[int, list[BitwardenEntry] | None]):
        """Takes the new search results and updates the results widget

        Args:
            new_results (list[BitwardenEntry]): _description_
        """

        request_id, results = data

        if not results or request_id <= self.__last_result_id:
            return

        self.__last_result_id = request_id
        self.results_widget.update_entries(results)


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
        results = search(inp)
        self.results_ready.emit((request_id, results))


class SearchResults(QListWidget):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.__results: list[SearchResult] = []
        self.itemSelectionChanged.connect(self.selection_changed)

    def update_entries(self, results: list[BitwardenEntry]):
        self.clear()
        self.__results = [SearchResult(x) for x in results]
        for w in self.__results:
            self.addItem(w)
            self.setItemWidget(w, w.get_label())

    def selection_changed(self):
        # print(self.selectedItems())
        for result in cast(list[SearchResults], self.selectedItems()):
            print(result.item)

    def try_focus(self):
        """Attempts to take focus *if* there are any valid search results"""
        if not len(self.__results):
            return

        self.setFocus()
        self.__results[0].setSelected(True)

    def unfocus(self):
        if not self.hasFocus():
            return False

        self.clearFocus()
        self.clearSelection()

        # Allow only if we're at the top of the results (or have none)
        return not len(self.__results) or self.currentRow() == 0


class SearchResult(QListWidgetItem):
    def __init__(self, item: BitwardenEntry):
        super().__init__()
        self.item = item

        self.__label = QLabel(f"<b>{self.item.name}</b> - {self.item.user} - {self.item.uri}")
        self.__label.setTextFormat(Qt.TextFormat.RichText)

        self.setText(item.name)
        self.setSizeHint(self.__label.sizeHint())

    def get_label(self):
        return self.__label


class HotkeyGuide(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        # layout.
        layout.addWidget(self.__make_guide("Ctrl + C", "Copy username"))
        layout.addWidget(self.__make_guide("Ctrl + Shift + C", "Copy password"))
        layout.addWidget(self.__make_guide("→", "More Actions"))
        self.setLayout(layout)

    def __make_guide(self, keybind: str, text: str) -> QWidget:
        lbl = QLabel()
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setText(f"""
            <span>
                {keybind}
            </span>
            &nbsp; {text}
        """)
        return lbl
