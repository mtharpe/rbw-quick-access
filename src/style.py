"""
@author Jose Stovall | oitsjustjose

Theming: a libadwaita (GNOME) look that follows the desktop's light/dark preference, accent
color and interface font. On Linux these come from the XDG desktop portal (which also
works inside containers) and update live; elsewhere the Qt color scheme is used with
GNOME's default blue.
"""

from dataclasses import dataclass

from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QGuiApplication

from plat import IS_LINUX

PORTAL_SERVICE = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
PORTAL_SETTINGS = "org.freedesktop.portal.Settings"

# GNOME's default accent (blue)
DEFAULT_ACCENT = QColor("#3584e4")


@dataclass
class Theme:
    """libadwaita's named colors, resolved for light or dark"""

    dark: bool
    accent_bg: QColor
    window_bg: QColor
    window_fg: QColor
    view_bg: QColor
    font: QFont | None

    @property
    def accent_fg(self) -> QColor:
        """The accent as a text/outline color: lighter on dark, darker on light (as libadwaita)"""
        return self.accent_bg.lighter(140) if self.dark else self.accent_bg.darker(120)

    def fg_alpha(self, alpha: float) -> str:
        """The foreground color at the given opacity, as a QSS rgba()"""
        return rgba(self.window_fg, alpha)

    def dim_fg(self) -> QColor:
        """libadwaita's dimmed label color"""
        color = QColor(self.window_fg)
        color.setAlphaF(0.55)
        return color


def rgba(color: QColor, alpha: float = 1.0) -> str:
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {round(color.alphaF() * alpha * 255)})"


def make_theme(dark: bool, accent: QColor | None, font: QFont | None) -> Theme:
    if dark:
        return Theme(dark, accent or DEFAULT_ACCENT, QColor("#222226"), QColor("#ffffff"), QColor("#1d1d20"), font)
    return Theme(dark, accent or DEFAULT_ACCENT, QColor("#fafafb"), QColor(0, 0, 6, 204), QColor("#ffffff"), font)


def build_stylesheet(t: Theme) -> str:
    return f"""
* {{
    color: {rgba(t.window_fg)};
}}

QMainWindow, QDialog {{
    background: transparent;
}}

/* The window itself: a rounded card, like GNOME Shell's popups */
#card {{
    background-color: {rgba(t.window_bg)};
    border: 1px solid {t.fg_alpha(0.15)};
    border-radius: 12px;
}}

QDialog {{
    background-color: {rgba(t.window_bg)};
}}

QLineEdit, QKeySequenceEdit QLineEdit {{
    background-color: {t.fg_alpha(0.1)};
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 8px 10px;
    margin: 10px 10px 4px 10px;
    font-size: 15pt;
    selection-background-color: {rgba(t.accent_bg, 0.5)};
}}

QLineEdit:focus {{
    border: 2px solid {rgba(t.accent_fg, 0.5)};
}}

QKeySequenceEdit QLineEdit {{
    margin: 2px;
    font-size: 11pt;
}}

QListWidget {{
    background-color: transparent;
    border: none;
    padding: 0px 6px;
    margin: 4px 4px 0px 4px;
    outline: none;
}}

QListWidget::item {{
    border-radius: 8px;
    margin: 1px 0px;
}}

QListWidget::item:hover {{
    background-color: {t.fg_alpha(0.07)};
}}

/* libadwaita's selection in views */
QListWidget::item:selected {{
    background-color: {rgba(t.accent_bg, 0.25)};
}}

QPushButton {{
    background-color: {t.fg_alpha(0.1)};
    border: none;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {t.fg_alpha(0.15)};
}}

QPushButton:pressed {{
    background-color: {t.fg_alpha(0.3)};
}}

QPushButton:focus {{
    border: 2px solid {rgba(t.accent_fg, 0.5)};
}}

/* suggested-action */
QPushButton[default="true"], QPushButton#suggested {{
    background-color: {rgba(t.accent_bg)};
    color: #ffffff;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}

QScrollBar::handle:vertical {{
    background: {t.fg_alpha(0.2)};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
    height: 0px;
}}

QToolTip {{
    background-color: {rgba(QColor("#000000"), 0.8)};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}}

#dimmed {{
    color: {rgba(t.dim_fg())};
}}
"""


def keycap_html(t: Theme, keys: str) -> str:
    """A shortcut drawn as a GNOME-style keycap (rich text can't round corners, so a tinted box)"""
    return f'<span style="background-color: {t.fg_alpha(0.12)}; color: {rgba(t.window_fg)};">&nbsp;{keys}&nbsp;</span>'


def parse_gnome_font(name: str) -> QFont | None:
    """'Adwaita Sans 11' -> QFont('Adwaita Sans', 11pt)"""
    family, _, size = name.rpartition(" ")
    if not family or not size.replace(".", "", 1).isdigit():
        return None
    return QFont(family, round(float(size)))


class ThemeManager(QObject):
    """Holds the current Theme and re-applies it when the desktop appearance changes"""

    changed = pyqtSignal()

    def __init__(self, app: QGuiApplication) -> None:
        super().__init__(app)
        self.__app = app
        self.__portal = None
        if IS_LINUX:
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface

            bus = QDBusConnection.sessionBus()
            self.__portal = QDBusInterface(PORTAL_SERVICE, PORTAL_PATH, PORTAL_SETTINGS, bus)
            bus.connect(PORTAL_SERVICE, PORTAL_PATH, PORTAL_SETTINGS, "SettingChanged", self.__on_setting_changed)
        else:
            hints = app.styleHints()
            if hints:
                hints.colorSchemeChanged.connect(lambda _scheme: self.apply())
        self.theme = self.__read()

    def __read_portal(self, namespace: str, key: str):
        if not self.__portal or not self.__portal.isValid():
            return None
        reply = self.__portal.call("ReadOne", namespace, key)
        args = reply.arguments()
        return args[0] if args else None

    def __read(self) -> Theme:
        scheme = self.__read_portal("org.freedesktop.appearance", "color-scheme")
        if scheme is None:
            hints = self.__app.styleHints()
            dark = bool(hints and hints.colorScheme() == Qt.ColorScheme.Dark)
        else:
            # 0 = no preference (GNOME's default is light), 1 = dark, 2 = light
            dark = scheme == 1

        accent = None
        rgb = self.__read_portal("org.freedesktop.appearance", "accent-color")
        if isinstance(rgb, (list, tuple)) and len(rgb) == 3 and all(0 <= c <= 1 for c in rgb):
            accent = QColor.fromRgbF(*rgb)

        font = None
        font_name = self.__read_portal("org.gnome.desktop.interface", "font-name")
        if isinstance(font_name, str):
            font = parse_gnome_font(font_name)

        return make_theme(dark, accent, font)

    def apply(self) -> None:
        """Reads the desktop appearance and restyles the application"""
        self.theme = self.__read()
        if self.theme.font:
            self.__app.setFont(self.theme.font)
        self.__app.setStyleSheet(build_stylesheet(self.theme))
        self.changed.emit()

    @pyqtSlot("QDBusMessage")
    def __on_setting_changed(self, message) -> None:
        namespace, key = message.arguments()[:2]
        if (namespace, key) in {
            ("org.freedesktop.appearance", "color-scheme"),
            ("org.freedesktop.appearance", "accent-color"),
            ("org.gnome.desktop.interface", "font-name"),
        }:
            self.apply()


THEME_MANAGER: ThemeManager | None = None


def install_theme(app: QGuiApplication) -> ThemeManager:
    """Creates the global ThemeManager and applies the theme"""
    global THEME_MANAGER
    THEME_MANAGER = ThemeManager(app)
    THEME_MANAGER.apply()
    return THEME_MANAGER


def current_theme() -> Theme:
    """The theme in use (light defaults before install_theme runs)"""
    if THEME_MANAGER:
        return THEME_MANAGER.theme
    return make_theme(False, None, None)
