from threading import Thread

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QListWidget,
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

        layout = QVBoxLayout()

        self.search = SearchBox(self)
        layout.addWidget(self.search)
        self.entries = SearchResults(self)
        layout.addWidget(self.entries)

        layout_widget = QWidget()
        layout_widget.setLayout(layout)
        self.setCentralWidget(layout_widget)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Overrides the generalized keyPressEvent to handle it ourselves after super() is called
        Used to close the application when `esc` is pressed.

        Args:
            a0 (QKeyEvent | None): The keypress event, if valid
        """
        super().keyPressEvent(a0)
        if a0 and a0.key() == Qt.Key.Key_Escape:
            self.__app.quit()

    def on_search_results_updated(self, new_results: list[BitwardenEntry]):
        """Takes the new search results and updates the results widget

        Args:
            new_results (list[BitwardenEntry]): _description_
        """
        self.entries.update_entries(new_results)


class SearchBox(QLineEdit):
    def __init__(self, parent: MainWindow):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(640)
        self.setFixedHeight(72)
        self.textChanged.connect(self.on_input_changed)

        self.__main_window = parent

    def on_input_changed(self, inp: str):
        """Called when the text input is changed, spinning up a new thread to do the `rbw` query and update the results.

        Args:
            inp (str): the search query
        """

        Thread(target=self.__search, args=[inp]).start()

    def __search(self, inp: str):
        """A function just for the purpose of doing the search and notifying the parent of the new results

        Args:
            inp (str): the search query
        """
        results = search(inp)
        if not results:
            return

        self.__main_window.on_search_results_updated(results)


class SearchResults(QListWidget):
    def __init__(self, parent: MainWindow):
        super().__init__()

    def update_entries(self, entries: list[BitwardenEntry]):
        self.clear()
        self.addItems([x.name for x in entries])
