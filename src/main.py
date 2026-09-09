from signal import SIGINT, signal
from sys import argv, exit

from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer
from PyQt6.QtWidgets import QApplication

from gui import MainWindow
from ipc import SERVER_NAME, attach
from style import DEFAULT_STYLE


def main():
    """
    Creates a brand new Application instance and starts up a QLocalServer
        which listens for future websocket attaches. Also handles some
        really nasty SIGINT garbage with a functional workaround.
    """

    # Just in case there's a stale socket
    QLocalServer.removeServer(SERVER_NAME)

    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setStyleSheet(DEFAULT_STYLE)

    window = MainWindow()
    window.setMinimumHeight(0)
    # No longer show immediately -- rely on keybinds.
    # window.show()

    # Since the app is stuck in an `exec` loop and the `LocalServer` embedded
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
    attach() and exit(0)  # pyright: ignore[reportUnusedExpression] - again, this is easier on the eyes
    main()
