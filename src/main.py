from os import environ
from sys import argv
from threading import Thread

from PyQt6.QtCore import pyqtBoundSignal
from PyQt6.QtWidgets import QApplication
from websockets.sync import connection, server

from gui import MainWindow

PORT = int(environ.get("PORT", "15621"))


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


def ws_server(show_signal: pyqtBoundSignal):
    def __handler(_):
        # Ignore the number of messages coming in
        show_signal.emit()

    s = server.serve(__handler, "localhost", PORT)
    s.serve_forever()


def start_gui_server():
    """
    Creates a brand new Application instance and spins up a Websocket
    on a thread to keep an eye open for any "--show" events
    """
    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setStyleSheet(__get_style())

    window = MainWindow()
    window.setMinimumHeight(0)

    ws_thread = Thread(target=ws_server, args=[window.show_requested], daemon=True)
    ws_thread.start()

    app.exec()
    ws_thread.join()


if __name__ == "__main__":
    start_gui_server()
