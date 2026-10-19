"""
@author Jose Stovall | oitsjustjose

A wrapper around the various rbw commands, including caching for better performance
"""

from signal import SIGINT, signal
from sys import argv

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui import MainWindow
from gui.elements import DismissableDialog
from instance import InstanceServer, notify_running
from rbw import RbwNotFoundException
from style import DEFAULT_STYLE


def main():
    """
    Creates a brand new Application instance and starts up a QLocalServer
        which listens for future websocket attaches. Also handles some
        really nasty SIGINT garbage with a functional workaround.
    """

    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setDesktopFileName("rbw-quick-access")
    app.setStyleSheet(DEFAULT_STYLE)

    # Already running: have that instance show itself instead
    if notify_running():
        return

    try:
        window = MainWindow()
        window.setMinimumHeight(0)

        app.focusWindowChanged.connect(window.on_focus_window_changed)

        instance_server = InstanceServer(app)
        instance_server.show_requested.connect(window.show_and_activate)
        # `--background` starts hidden (e.g. at login); otherwise a launch means "show me"
        if "--background" not in argv:
            window.show_and_activate()

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
    except RbwNotFoundException:
        dlg = DismissableDialog(
            None,
            "Failed to find rbw!",
            """
            <style>
                code {
                    background-color: #1a1b26; 
                    color: #f7768e; 
                    border-radius: 8px; 
                    padding: 8px;
                }
            </style>
            
            <div style="color: #c0caf5; font-size: 20px; text-align: center;">
                The <code>rbw</code> executable could not be found. Install and add it to your <code>PATH</code>, then restart <code>rbw-quick-access</code>.
            </div>
            """,
        )
        dlg.setStyleSheet(DEFAULT_STYLE)
        dlg.exec()
        app.quit()


if __name__ == "__main__":
    main()
