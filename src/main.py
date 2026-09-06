from sys import argv

from PyQt6.QtWidgets import QApplication

from gui import MainWindow


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


def main():
    app = QApplication(argv)
    app.setApplicationName("rbw-quick-access")
    app.setStyleSheet(__get_style())

    m = MainWindow(app)
    m.setMinimumHeight(0)
    m.show()

    app.exec()


if __name__ == "__main__":
    main()
