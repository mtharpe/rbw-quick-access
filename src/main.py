from signal import SIGINT, signal
from sys import argv, exit

from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer
from PyQt6.QtWidgets import QApplication

from gui import MainWindow
from ipc import SERVER_NAME, attach


def __get_style() -> str:
    """Does weird build-time checking to ensure that the style is
     loaded from `styles.qss` when needed, but isn't when it's not.

    Returns:
        str: The QSS style
    """
    # DO NOT TOUCH -- contents of `style.qss` are put between the
    #  two sentinels below at build-time.
    style = """
    /* # STYLE_START */
    /* # STYLE_END */
    """.strip()

    # If the style was touched, we'll have more than 2 lines, since we
    #  know we'll have 2 for the sentinels
    if len(style.split("\n")) > 2:
        return style

    # Open from disk then
    with open("style.qss", "r") as fh:
        return fh.read()


def make_gui_server():
    """
    Creates a brand new Application instance and spins up a Websocket
    on a thread to keep an eye open for any "--show" events
    """

    # Just in case there's a stale socket
    QLocalServer.removeServer(SERVER_NAME)

    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setStyleSheet(__get_style())

    window = MainWindow()
    window.setMinimumHeight(0)
    window.show()

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
    make_gui_server()
