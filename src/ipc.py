# from PyQt6.QtCore import QByteArray
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QWidget

SERVER_NAME = "rbw-quick-access"


class LocalServer(QLocalServer):
    """Really basic local server impl - mostly NOOP"""

    def __init__(self, widget: QWidget):
        super().__init__(widget)
        self.widget = widget
        self.newConnection.connect(self.__on_connection)

        if not self.listen(SERVER_NAME):
            raise RuntimeError(self.errorString())

    def __on_connection(self):
        """A straight-forward connection wrapper/handler"""
        sock = self.nextPendingConnection()
        if not sock:
            return
        sock.readyRead.connect(lambda: self.__handle_socket(sock))

    def __handle_socket(self, sock: QLocalSocket):
        """Another straight forward handler, for sockets this time"""
        # message = bytes(socket.readAll()).decode() -- ???
        msg = sock.readAll().data().decode()

        if msg == "show":
            self.widget.show()
            self.widget.raise_()
            self.widget.activateWindow()
        # These are meant to be
        sock.disconnectFromServer()


def attach(timeout_ms=100) -> bool:
    """Attaches to the already running local instance if it's running.

    Args:
        timeout_ms (int, optional): Time in millis before the connection to the server times out. Defaults to 100

    Returns:
        bool: whether the connection succeeded
    """
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)

    if not sock.waitForConnected(timeout_ms):
        return False

    sock.write(b"show")
    sock.waitForBytesWritten(timeout_ms)
    sock.disconnectFromServer()
    return True
