from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF


class MaterialIcons:
    """
    Generates resolution-independent, vector-drawn Material Design icons in memory.
    Ensures zero external asset dependencies and crisp rendering on High-DPI screens.
    """

    @staticmethod
    def app_tray_icon(size: int = 64) -> QIcon:
        """Draws a refined Word-blue Material document tray icon with badge."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Base folded paper shape
        path = QPainterPath()
        w = size * 0.72
        h = size * 0.88
        x = (size - w) / 2
        y = (size - h) / 2
        fold = size * 0.22

        path.moveTo(x, y + 6)
        path.lineTo(x + w - fold, y + 6)
        path.lineTo(x + w, y + 6 + fold)
        path.lineTo(x + w, y + h)
        path.lineTo(x, y + h)
        path.closeSubpath()

        # Paper background (Gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#006399"))  # MD3 Primary Blue
        painter.drawPath(path)

        # Fold corner
        fold_path = QPainterPath()
        fold_path.moveTo(x + w - fold, y + 6)
        fold_path.lineTo(x + w - fold, y + 6 + fold)
        fold_path.lineTo(x + w, y + 6 + fold)
        fold_path.closeSubpath()
        painter.setBrush(QColor("#CCE5FF"))
        painter.drawPath(fold_path)

        # Inner text lines
        painter.setPen(QPen(QColor("#FFFFFF"), size * 0.06, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        line_x1 = x + w * 0.22
        line_x2 = x + w * 0.78
        painter.drawLine(QPointF(line_x1, y + h * 0.42), QPointF(line_x2, y + h * 0.42))
        painter.drawLine(QPointF(line_x1, y + h * 0.58), QPointF(line_x2, y + h * 0.58))
        painter.drawLine(QPointF(line_x1, y + h * 0.74), QPointF(line_x1 + w * 0.35, y + h * 0.74))

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def drag_upload_icon(size: int = 72) -> QPixmap:
        """Draws a cloud upload / file drop icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Circular container
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#E0F2FE"))  # Light cyan/blue container
        painter.drawEllipse(QRectF(4, 4, size - 8, size - 8))

        # Arrow Up
        painter.setPen(QPen(QColor("#0284C7"), size * 0.08, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        cx = size / 2
        cy = size / 2

        # Up arrow stem
        painter.drawLine(QPointF(cx, cy + size * 0.18), QPointF(cx, cy - size * 0.16))
        # Arrow heads
        head_w = size * 0.16
        painter.drawLine(QPointF(cx - head_w, cy - size * 0.02), QPointF(cx, cy - size * 0.16))
        painter.drawLine(QPointF(cx + head_w, cy - size * 0.02), QPointF(cx, cy - size * 0.16))

        # Bottom tray line
        tray_w = size * 0.24
        painter.drawLine(QPointF(cx - tray_w, cy + size * 0.24), QPointF(cx + tray_w, cy + size * 0.24))

        painter.end()
        return pixmap

    @staticmethod
    def clipboard_icon(size: int = 24) -> QIcon:
        """Draws a clipboard icon for paste button."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#006399"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Clipboard body
        painter.drawRoundedRect(QRectF(4, 6, 16, 15), 2.5, 2.5)
        # Clip top handle
        painter.setBrush(QColor("#006399"))
        painter.drawRoundedRect(QRectF(8, 3, 8, 4), 1.5, 1.5)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def file_open_icon(size: int = 20) -> QIcon:
        """Icon for opening file."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#0284C7"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(QRectF(3, 3, 14, 14), 2, 2)
        # diagonal arrow
        painter.drawLine(QPointF(8, 12), QPointF(13, 7))
        painter.drawLine(QPointF(9, 7), QPointF(13, 7))
        painter.drawLine(QPointF(13, 11), QPointF(13, 7))

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def folder_open_icon(size: int = 20) -> QIcon:
        """Icon for opening directory."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#475569"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Folder outline
        f_path = QPainterPath()
        f_path.moveTo(3, 6)
        f_path.lineTo(7, 6)
        f_path.lineTo(9, 8)
        f_path.lineTo(17, 8)
        f_path.lineTo(17, 16)
        f_path.lineTo(3, 16)
        f_path.closeSubpath()
        painter.drawPath(f_path)

        painter.end()
        return QIcon(pixmap)
