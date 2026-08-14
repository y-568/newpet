"""云朵回答框 — 可爱蓬松风格，无边框独立窗口，内容超出时自动滚动"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication,
                                QScrollArea)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor


class CloudWidget(QWidget):
    """云朵回答框 — 扩展至最大尺寸后通过滚动查看内容"""

    MAX_W, MAX_H = 420, 380  # 云朵最大宽高

    def __init__(self, parent=None, standalone: bool = False):
        super().__init__(parent)
        self._standalone = standalone

        if standalone:
            self._setup_standalone_window()

        self.setMinimumSize(280, 120)
        self._dragging = False
        self._drag_offset = QPoint()

        # ── 外层布局 ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(35, 30, 35, 30)

        # ── 滚动区域 ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 80);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(180, 200, 230, 200);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # ── 文本标签 ──
        self.label = QLabel("💬 等待你的提问...")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #3d3d3d;
                background: transparent;
                border: none;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                line-height: 1.6;
                padding: 4px;
            }
        """)
        self.scroll.setWidget(self.label)
        outer.addWidget(self.scroll)

        self._current_text = ""

    def _setup_standalone_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

    # ── 核心：自适应大小 + 最大限制 ────────────────

    def set_text(self, text: str):
        """更新文字，窗口自适应扩展，达到上限后出现滚动条"""
        self._current_text = text
        self.label.setText(text)

        # 计算 label 需要的理想尺寸
        self.label.adjustSize()
        label_w = self.label.sizeHint().width()
        label_h = self.label.sizeHint().height()

        # 目标云朵尺寸 = label 尺寸 + 内边距 (35+35 水平, 30+30 垂直)
        target_w = min(label_w + 70, self.MAX_W)
        target_h = min(label_h + 60, self.MAX_H)
        target_w = max(target_w, self.minimumWidth())
        target_h = max(target_h, self.minimumHeight())

        self.resize(target_w, target_h)

    def clear(self):
        self._current_text = ""
        self.label.setText("💬 等待你的提问...")
        self.resize(300, 130)

    # ── 拖动 ──────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()

    # ── 云朵绘制 ──────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        cx = w / 2

        path = QPainterPath()
        # 底部
        path.moveTo(20, h - 15)
        path.quadTo(cx, h + 15, w - 20, h - 15)
        # 右侧
        path.quadTo(w + 15, h - 25, w - 10, h - 45)
        path.quadTo(w + 10, h - 75, w - 25, h - 85)
        # 右上
        path.quadTo(w - 10, h - 105, w - 40, h - 100)
        path.quadTo(w - 35, h - 115, cx + 50, h - 105)
        # 顶部
        path.quadTo(cx + 30, h - 125, cx, h - 130)
        path.quadTo(cx - 30, h - 125, cx - 50, h - 105)
        path.quadTo(w * 0.25, h - 115, w * 0.2, h - 100)
        # 左上
        path.quadTo(10, h - 105, 25, h - 85)
        path.quadTo(-10, h - 75, 10, h - 45)
        # 左侧
        path.quadTo(-15, h - 25, 20, h - 15)
        path.closeSubpath()

        # 阴影
        sp = QPainterPath(path)
        sp.translate(2, 3)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 15))
        painter.drawPath(sp)

        # 主体
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.drawPath(path)

        # 高光
        hp1 = QPainterPath()
        hp1.addEllipse(w * 0.25, h * 0.15, w * 0.2, h * 0.18)
        painter.setBrush(QColor(255, 255, 255, 80))
        painter.drawPath(hp1)

        hp2 = QPainterPath()
        hp2.addEllipse(w * 0.65, h * 0.12, w * 0.12, h * 0.12)
        painter.setBrush(QColor(255, 255, 255, 60))
        painter.drawPath(hp2)


if __name__ == "__main__":
    app = QApplication([])
    window = CloudWidget(standalone=True)
    window.set_text("这是一段测试文本，用来验证云朵自动扩展。\n" * 30)
    window.show()
    app.exec()
