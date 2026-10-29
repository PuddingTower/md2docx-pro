import os
import subprocess
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QFrame, QFileDialog,
    QCheckBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent, QAction, QKeySequence

from .styles import MaterialTheme
from .icons import MaterialIcons
from .tray import SystemTrayController

try:
    from core.converter import DocumentConverter, ConversionResult
except ImportError:
    from ..core.converter import DocumentConverter, ConversionResult


class ConvertWorker(QThread):
    """
    Background worker thread to perform conversions without freezing the GUI.
    """
    task_started = pyqtSignal(str)
    task_finished = pyqtSignal(ConversionResult)
    all_finished = pyqtSignal(int, int)  # success_count, fail_count

    def __init__(self, converter: DocumentConverter, tasks: List[str], preset: str, is_text: bool = False, text_content: str = ""):
        super().__init__()
        self.converter = converter
        self.tasks = tasks
        self.preset = preset
        self.is_text = is_text
        self.text_content = text_content

    def run(self):
        success_cnt = 0
        fail_cnt = 0

        if self.is_text:
            self.task_started.emit("剪贴板文本")
            result = self.converter.convert_text(self.text_content, preset=self.preset)
            if result.success:
                success_cnt += 1
            else:
                fail_cnt += 1
            self.task_finished.emit(result)
        else:
            for file_path in self.tasks:
                self.task_started.emit(file_path)
                result = self.converter.convert_file(file_path, preset=self.preset)
                if result.success:
                    success_cnt += 1
                else:
                    fail_cnt += 1
                self.task_finished.emit(result)

        self.all_finished.emit(success_cnt, fail_cnt)


class DropZoneWidget(QFrame):
    """
    Material 3 Hero Drop Area with visual drag-over feedback.
    """
    files_dropped = pyqtSignal(list)
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZoneFrame")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(6)

        # Upload Cloud Icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(MaterialIcons.drag_upload_icon(64))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel("拖拽一个或多个 .md 文件至此")
        self.title_label.setObjectName("DropZoneTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Description
        self.desc_label = QLabel("或点击此区域浏览选择 · 支持拖入包含 md 的文件夹 · 支持按 Ctrl+V 粘贴")
        self.desc_label.setObjectName("DropZoneDesc")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.desc_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragOver", "true")
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragOver", "false")
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragOver", "false")
        self.style().polish(self)

        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            local_path = url.toLocalFile()
            if os.path.isfile(local_path) and local_path.lower().endswith('.md'):
                file_paths.append(local_path)
            elif os.path.isdir(local_path):
                # Traverse folder for .md
                for root, _, files in os.walk(local_path):
                    for f in files:
                        if f.lower().endswith('.md'):
                            file_paths.append(os.path.join(root, f))

        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class TaskItemCard(QFrame):
    """
    Displays a converted document record with quick actions (Open Word, Open Folder).
    """
    def __init__(self, result: ConversionResult, parent=None):
        super().__init__(parent)
        self.setProperty("class", "task-item-card")
        self.result = result

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # File Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name = os.path.basename(result.output_path) if result.output_path else os.path.basename(result.input_source)
        self.lbl_name = QLabel(name)
        self.lbl_name.setProperty("class", "task-filename")
        info_layout.addWidget(self.lbl_name)

        if result.success:
            size_kb = round(result.file_size_bytes / 1024, 1)
            detail_text = f"耗时 {result.elapsed_time}s · 大小 {size_kb} KB · 目录: {os.path.dirname(result.output_path)}"
        else:
            detail_text = f"失败: {result.error_message}"

        self.lbl_path = QLabel(detail_text)
        self.lbl_path.setProperty("class", "task-path")
        self.lbl_path.setToolTip(result.output_path or result.input_source)
        info_layout.addWidget(self.lbl_path)

        layout.addLayout(info_layout, 1)

        # Badge
        badge = QLabel("转换成功" if result.success else "失败")
        badge.setProperty("class", "task-badge-success" if result.success else "task-badge-error")
        layout.addWidget(badge)

        # Quick Actions
        if result.success and result.output_path and os.path.exists(result.output_path):
            self.btn_open = QPushButton("打开 Word")
            self.btn_open.setProperty("class", "icon-btn")
            self.btn_open.setIcon(MaterialIcons.file_open_icon(14))
            self.btn_open.clicked.connect(self._open_docx)
            layout.addWidget(self.btn_open)

            self.btn_folder = QPushButton("定位目录")
            self.btn_folder.setProperty("class", "icon-btn")
            self.btn_folder.setIcon(MaterialIcons.folder_open_icon(14))
            self.btn_folder.clicked.connect(self._open_folder)
            layout.addWidget(self.btn_folder)

    def _open_docx(self):
        try:
            os.startfile(self.result.output_path)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件: {e}")

    def _open_folder(self):
        try:
            # Highlight file in Windows Explorer
            subprocess.run(['explorer.exe', '/select,', os.path.normpath(self.result.output_path)])
        except Exception:
            try:
                os.startfile(os.path.dirname(self.result.output_path))
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开文件夹: {e}")


class MainWindow(QMainWindow):
    """
    MD3 Styled Main Window with Tray Controller and Instant Converter.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown to DOCX")
        self.setWindowIcon(MaterialIcons.app_tray_icon(64))
        self.resize(700, 620)
        self.setMinimumSize(580, 500)

        self.converter = DocumentConverter()
        self.worker: Optional[ConvertWorker] = None
        self.has_shown_minimize_tip = False

        self._init_ui()
        self._init_shortcuts()
        self.tray = SystemTrayController(self, on_clipboard_convert=self.convert_from_clipboard)

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # --- Top Header Bar ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(12, 8, 12, 8)

        # Title Info
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("Markdown to DOCX")
        lbl_title.setObjectName("AppTitle")
        lbl_sub = QLabel("轻量后台排版引擎 · 自动就地生成 Word 文档")
        lbl_sub.setObjectName("AppSubtitle")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        # Status Pill
        lbl_status = QLabel("● 后台就绪")
        lbl_status.setObjectName("StatusPill")
        h_layout.addWidget(lbl_status)

        # Preset Selector
        self.combo_preset = QComboBox()
        self.combo_preset.addItem("现代商务 (Modern)", "modern")
        self.combo_preset.addItem("学术科研 (Academic)", "academic")
        self.combo_preset.addItem("极简科技 (Minimal)", "minimal")
        h_layout.addWidget(self.combo_preset)

        main_layout.addWidget(header_frame)

        # --- Hero Drop Zone ---
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_dropped.connect(self.start_batch_conversion)
        self.drop_zone.clicked.connect(self.browse_and_convert)
        main_layout.addWidget(self.drop_zone)

        # --- Quick Actions Bar ---
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        # Paste & Convert Button
        self.btn_paste = QPushButton("从剪贴板粘贴并转换 (Ctrl+V)")
        self.btn_paste.setProperty("class", "primary-btn")
        self.btn_paste.setIcon(MaterialIcons.clipboard_icon(18))
        self.btn_paste.clicked.connect(self.convert_from_clipboard)
        action_bar.addWidget(self.btn_paste)

        # Select Files Button
        self.btn_browse = QPushButton("选择 .md 文件")
        self.btn_browse.setProperty("class", "outlined-btn")
        self.btn_browse.clicked.connect(self.browse_and_convert)
        action_bar.addWidget(self.btn_browse)

        action_bar.addStretch()

        # Minimize to Tray Button
        self.btn_minimize = QPushButton("最小化到托盘")
        self.btn_minimize.setProperty("class", "outlined-btn")
        self.btn_minimize.clicked.connect(self.hide)
        action_bar.addWidget(self.btn_minimize)

        main_layout.addLayout(action_bar)

        # --- History Cards Container ---
        history_box = QFrame()
        history_box.setObjectName("HistoryContainer")
        hist_vlayout = QVBoxLayout(history_box)
        hist_vlayout.setContentsMargins(10, 8, 10, 8)
        hist_vlayout.setSpacing(8)

        # Header of History
        hist_header = QHBoxLayout()
        self.lbl_hist_title = QLabel("转换记录与快速操作")
        self.lbl_hist_title.setObjectName("HistoryHeaderLabel")
        hist_header.addWidget(self.lbl_hist_title)

        hist_header.addStretch()

        self.btn_clear = QPushButton("清空记录")
        self.btn_clear.setProperty("class", "icon-btn")
        self.btn_clear.clicked.connect(self._clear_history)
        hist_header.addWidget(self.btn_clear)

        hist_vlayout.addLayout(hist_header)

        # Scroll area for items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        hist_vlayout.addWidget(self.scroll_area, 1)

        main_layout.addWidget(history_box, 1)

    def _init_shortcuts(self):
        """Global Ctrl+V shortcut for paste & convert."""
        self.paste_action = QAction(self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.convert_from_clipboard)
        self.addAction(self.paste_action)

    def browse_and_convert(self):
        """Opens file dialog for choosing .md files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择 Markdown 文件",
            os.getcwd(),
            "Markdown Files (*.md);;All Files (*.*)"
        )
        if files:
            self.start_batch_conversion(files)

    def convert_from_clipboard(self):
        """
        Handles clipboard conversion:
        1. If clipboard contains copied files (Explorer Ctrl+C), extracts .md and converts in-place!
        2. If clipboard contains plain text, converts text to docx in Desktop.
        """
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        # Case 1: Copied files
        if mime.hasUrls():
            file_paths = []
            for url in mime.urls():
                p = url.toLocalFile()
                if os.path.isfile(p) and p.lower().endswith('.md'):
                    file_paths.append(p)
                elif os.path.isdir(p):
                    for root, _, files in os.walk(p):
                        for f in files:
                            if f.lower().endswith('.md'):
                                file_paths.append(os.path.join(root, f))
            if file_paths:
                self.start_batch_conversion(file_paths)
                return

        # Case 2: Plain text
        text = clipboard.text()
        if text and text.strip():
            preset = self.combo_preset.currentData()
            self._start_worker(tasks=[], preset=preset, is_text=True, text_content=text)
        else:
            QMessageBox.information(self, "提示", "剪贴板中未检测到 .md 文件或 Markdown 文本内容。")

    def start_batch_conversion(self, file_paths: List[str]):
        """Starts batch file conversion in the background worker."""
        if not file_paths:
            return
        preset = self.combo_preset.currentData()
        self._start_worker(tasks=file_paths, preset=preset, is_text=False)

    def _start_worker(self, tasks: List[str], preset: str, is_text: bool = False, text_content: str = ""):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, "忙碌", "正在进行转换，请稍候...")
            return

        self.btn_paste.setEnabled(False)
        self.drop_zone.setEnabled(False)

        self.worker = ConvertWorker(
            converter=self.converter,
            tasks=tasks,
            preset=preset,
            is_text=is_text,
            text_content=text_content
        )
        self.worker.task_finished.connect(self._on_task_finished)
        self.worker.all_finished.connect(self._on_all_finished)
        self.worker.start()

    def _on_task_finished(self, result: ConversionResult):
        # Insert card into history
        card = TaskItemCard(result)
        # Insert at the top of scroll layout
        self.cards_layout.insertWidget(0, card)

        # Notify tray
        if result.success:
            doc_name = os.path.basename(result.output_path)
            self.tray.notify("Word 转换完成", f"{doc_name} 已在对应目录下生成", docx_path=result.output_path)
        else:
            self.tray.notify("转换失败", f"{os.path.basename(result.input_source)}: {result.error_message}")

    def _on_all_finished(self, success_cnt: int, fail_cnt: int):
        self.btn_paste.setEnabled(True)
        self.drop_zone.setEnabled(True)
        self.worker = None

    def _clear_history(self):
        # Remove all item cards except stretch
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def closeEvent(self, event):
        """
        Intercept close: Hide to system tray instead of quitting.
        """
        event.ignore()
        self.hide()
        if not self.has_shown_minimize_tip:
            self.tray.notify("程序已常驻系统托盘", "点击或双击右下角图标即可重新唤出界面。")
            self.has_shown_minimize_tip = True
