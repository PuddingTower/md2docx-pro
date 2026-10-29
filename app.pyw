import sys
import os

# Ensure package import path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.styles import MaterialTheme
from ui.main_window import MainWindow


def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("MarkdownToDOCX")
    app.setOrganizationName("AirfoilDesign")

    # Important: Do NOT exit app when main window is hidden/closed!
    # Keeps it running smoothly in the system tray.
    app.setQuitOnLastWindowClosed(False)

    # Apply Material Design 3 theme
    app.setStyleSheet(MaterialTheme.get_application_qss())

    window = MainWindow()

    # If launched with --tray or --minimized, start directly in tray
    if "--tray" in sys.argv or "--minimized" in sys.argv:
        window.hide()
        window.tray.notify("Markdown 转 Word 已启动", "程序已在后台托盘常驻就绪。")
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
