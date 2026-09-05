from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QLineEdit, QMainWindow, QSizePolicy, QWidget

from rbw import search


class MainWindow(QMainWindow):

    def __init__(self, app: QApplication):
        super().__init__()
        self.__app = app
        self.search = SearchBox(self)
        self.setCentralWidget(self.search)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Overrides the generalized keyPressEvent to handle it ourselves after super() is called
        Used to close the application when `esc` is pressed.

        Args:
            a0 (QKeyEvent | None): The keypress event, if valid
        """
        super().keyPressEvent(a0)
        if a0 and a0.key() == Qt.Key.Key_Escape:
            self.__app.quit()


class SearchBox(QLineEdit):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(640)
        self.setFixedHeight(72)
        self.textChanged.connect(self.on_input_changed)

    def on_input_changed(self, inp: str):
        results = search(inp)
        # print(len(results))
        # print(results)
