"""
Single-instance handling: running `rbw-quick-access` while it's already running asks the
running copy to show itself, so a desktop shortcut that runs the command acts as the
global hotkey.
"""

import os

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = f"rbw-quick-access-{os.getuid()}"
SHOW_MESSAGE = b"show\n"


def notify_running() -> bool:
    """Asks an already-running instance to show itself

    Returns:
        bool: True if an instance answered (and this one should exit), False otherwise
    """
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if not sock.waitForConnected(500):
        return False

    sock.write(SHOW_MESSAGE)
    sock.waitForBytesWritten(500)
    sock.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Listens for later launches and emits show_requested for each one"""

    show_requested = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.__server = QLocalServer(self)
        # A crashed instance leaves its socket behind, which would make listen() fail
        QLocalServer.removeServer(SERVER_NAME)
        self.__server.listen(SERVER_NAME)
        self.__server.newConnection.connect(self.__on_new_connection)

    def __on_new_connection(self) -> None:
        while conn := self.__server.nextPendingConnection():
            conn.readyRead.connect(lambda c=conn: self.__on_ready_read(c))
            conn.disconnected.connect(conn.deleteLater)

    def __on_ready_read(self, conn: QLocalSocket) -> None:
        if bytes(conn.readAll()).startswith(SHOW_MESSAGE.strip()):
            self.show_requested.emit()
