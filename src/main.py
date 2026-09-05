from sys import argv

from PyQt6.QtWidgets import QApplication

from qt import MainWindow


def main():
    # TODO: Singleton tracking -- save a PID somewhere or something? Not sure..
    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")

    with open("style.qss", "r") as fh:
        style = fh.read()
        app.setStyleSheet(style)

    m = MainWindow(app)
    m.setMinimumHeight(0)
    m.show()

    app.exec()


if __name__ == "__main__":
    main()
