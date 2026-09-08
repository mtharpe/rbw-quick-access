"""
@author Jose Stovall | oitsjustjose
At some point this will contain more than a const str
    such as config reading for the current style vals.
    Until then, it does just that.
"""

DEFAULT_STYLE = """
* {
    color: #c0caf5;
}

*:focus {
    border: 4px solid #7dcfff;
}

QHBoxLayout {
    background-color: #414868;
}

QMainWindow {
    background-color: #16161e;
}

QLineEdit {
    background-color: #1a1b26;
    border: 4px solid #414868;
    border-radius: 8px;
    /* Same padding as border rad */
    padding: 8px;

    margin: 12px;
    font-size: 20px;
}

QListWidget {
    background-color: #1a1b26;
    border: 4px solid #414868;
    border-radius: 8px;
    /* Same padding as border rad */
    padding: 8px;

    margin: 12px;
    font-size: 18px;
}

QListWidget::item {
    padding: 4px;
    border-radius: 8px;
}   

QListWidget::item::selected {
    /* TEXT COLOR IS HANDLED IN THE DELEGATE */
    background-color: #bb9af7;
}
"""
