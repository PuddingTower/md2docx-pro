import os
import subprocess
from typing import Callable, Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon
from .icons import MaterialIcons


class SystemTrayController:
    """
    Manages background presence, system tray icon, context menus,
    and native desktop notification bubbles.
    """

    def __init__(self, main_window, on_clipboard_convert: Optional[Callable] = None):
        self.main_window = main_window
        self.on_clipboard_convert = on_clipboard_convert
        self.last_output_dir = os.path.expanduser("~")
        self.last_output_file = ""

        self.tray_icon = QSystemTrayIcon(main_window)
        self.icon = MaterialIcons.app_tray_icon(32)
        self.tray_icon.setIcon(self.icon)
        self.tray_icon.setToolTip("Markdown 转 Word (常驻后台)")

        self._build_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.messageClicked.connect(self._on_notification_clicked)
        self.tray_icon.show()

    def _build_menu(self):
        menu = QMenu()

        # Show Window
        self.act_show = QAction("显示主窗口", menu)
        self.act_show.triggered.connect(self.show_main_window)
        menu.addAction(self.act_show)

        # Convert Clipboard
        if self.on_clipboard_convert:
            self.act_clipboard = QAction("转换剪贴板", menu)
            self.act_clipboard.setIcon(MaterialIcons.clipboard_icon(16))
            self.act_clipboard.triggered.connect(self.on_clipboard_convert)
            menu.addAction(self.act_clipboard)

        menu.addSeparator()

        # Open Last Output Folder
        self.act_open_dir = QAction("打开输出目录", menu)
        self.act_open_dir.setIcon(MaterialIcons.folder_open_icon(16))
        self.act_open_dir.triggered.connect(self._open_last_folder)
        menu.addAction(self.act_open_dir)

        menu.addSeparator()

        # Exit
        self.act_exit = QAction("退出程序", menu)
        self.act_exit.triggered.connect(self._on_exit_app)
        menu.addAction(self.act_exit)

        self.tray_icon.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in [QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick]:
            if self.main_window.isVisible():
                if self.main_window.isActiveWindow():
                    self.main_window.hide()
                else:
                    self.main_window.raise_()
                    self.main_window.activateWindow()
            else:
                self.show_main_window()

    def show_main_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def notify(self, title: str, message: str, docx_path: str = ""):
        """Pops up a native Windows notification bubble."""
        if docx_path:
            self.last_output_file = docx_path
            self.last_output_dir = os.path.dirname(docx_path)
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _on_notification_clicked(self):
        """When notification clicked, open the converted docx file."""
        if self.last_output_file and os.path.exists(self.last_output_file):
            try:
                os.startfile(self.last_output_file)
            except Exception:
                pass

    def _open_last_folder(self):
        target = self.last_output_dir if os.path.exists(self.last_output_dir) else os.getcwd()
        try:
            os.startfile(target)
        except Exception:
            subprocess.Popen(['explorer.exe', target])

    def _on_exit_app(self):
        from PyQt6.QtWidgets import QApplication
        self.tray_icon.hide()
        QApplication.quit()
