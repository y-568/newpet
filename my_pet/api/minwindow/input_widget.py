"""用户输入组件 — 无边框独立窗口，玻璃质感背景"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                                QLineEdit, QLabel, QHBoxLayout, QPushButton, QApplication)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor


class InputOutputWidget(QWidget):
    """用户输入组件，支持嵌入和独立窗口两种模式"""

    send_message = Signal(str)
    gear_clicked = Signal()  # 齿轮按钮点击

    def __init__(self, parent=None, standalone: bool = False):
        """
        Args:
            parent: 父组件
            standalone: True=作为独立无边框窗口运行
        """
        super().__init__(parent)
        self._standalone = standalone
        self._dragging = False
        self._drag_offset = QPoint()

        # 独立窗口设置
        if standalone:
            self._setup_standalone_window()

        self._setup_ui()

    def _setup_standalone_window(self):
        """配置为独立无边框窗口"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(340, 80)

    def _setup_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # 输入行：输入框 + 发送按钮
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("在这里输入你的问题...")
        self.input_box.setMinimumHeight(36)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 210);
                border: 1.5px solid rgba(180, 210, 255, 200);
                border-radius: 18px;
                padding: 5px 15px;
                font-size: 14px;
                color: #333;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }
            QLineEdit:focus {
                border-color: rgba(100, 150, 255, 240);
                background: rgba(255, 255, 255, 245);
            }
        """)

        self.btn_send = QPushButton("✨")
        self.btn_send.setFixedSize(36, 36)
        self.btn_send.setToolTip("发送消息")
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: rgba(150, 200, 255, 210);
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(120, 180, 255, 240);
            }
            QPushButton:pressed {
                background: rgba(90, 150, 255, 255);
            }
        """)

        input_layout.addWidget(self.input_box, stretch=1)

        # 齿轮按钮
        self.btn_gear = QPushButton("⚙️")
        self.btn_gear.setFixedSize(32, 32)
        self.btn_gear.setCursor(Qt.PointingHandCursor)
        self.btn_gear.setToolTip("菜单")
        self.btn_gear.setStyleSheet("""
            QPushButton {
                background: rgba(200, 210, 230, 160);
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(170, 190, 220, 230);
            }
            QPushButton:pressed {
                background: rgba(140, 160, 210, 250);
            }
        """)
        input_layout.addWidget(self.btn_gear)

        input_layout.addWidget(self.btn_send)
        layout.addLayout(input_layout)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: rgba(150, 150, 150, 200);
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                background: transparent;
            }
        """)
        layout.addWidget(self.status_label)

        # 连接信号
        self.input_box.returnPressed.connect(self._emit_message)
        self.btn_send.clicked.connect(self._emit_message)
        self.btn_gear.clicked.connect(self.gear_clicked.emit)

    def _emit_message(self):
        """发送输入框内容"""
        text = self.input_box.text().strip()
        if text:
            self.send_message.emit(text)
            self.input_box.clear()
            self.input_box.setFocus()

    def set_status(self, text: str):
        self.status_label.setText(text)

    def clear_status(self):
        self.status_label.setText("")

    def set_enabled(self, enabled: bool):
        self.input_box.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)

    # ── 拖动支持 ──────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()

    # ── 玻璃态背景绘制 ────────────────────────────────

    def paintEvent(self, event):
        """绘制半透明磨砂玻璃背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)

        # 半透明玻璃背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 248, 255, 210))
        painter.drawPath(path)

        # 细边框
        painter.setPen(QColor(200, 220, 255, 150))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 16, 16)


if __name__ == "__main__":
    app = QApplication([])
    window = InputOutputWidget(standalone=True)
    window.show()
    app.exec()
