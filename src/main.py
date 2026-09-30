"""
@author Jose Stovall | oitsjustjose

A wrapper around the various rbw commands, including caching for better performance
"""

from signal import SIGINT, signal
from sys import argv

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui import MainWindow
from style import DEFAULT_STYLE


def main():
    """
    Creates a brand new Application instance and starts up a QLocalServer
        which listens for future websocket attaches. Also handles some
        really nasty SIGINT garbage with a functional workaround.
    """

    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setStyleSheet(DEFAULT_STYLE)

    window = MainWindow()
    window.setMinimumHeight(0)

    app.focusWindowChanged.connect(window.on_focus_window_changed)

    # Since the app is stuck in an `exec` loop and the `hotkey` embedded loop
    # in the MainWindow is running, we need to handle SIGINT differently. Ugh.
    signal(SIGINT, lambda *_: app.quit())
    # Apparently this is the QT-styled way of handling this? Gross.
    #  The logic is, this timer causes QT to come back from C++ land and
    #  notice that the app was told to quit in the SIGINT handler above.
    # It's not obvious anywhere, but this timer *loops*. It's otherwise NOOP
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    app.exec()


if __name__ == "__main__":
    main()
