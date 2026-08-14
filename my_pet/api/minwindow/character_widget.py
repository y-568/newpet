"""动漫角色立绘窗口 — 无边框、透明、可拖动"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QPainter


class CharacterWidget(QWidget):
    """显示动漫人物 PNG 立绘的无边框窗口"""

    def __init__(self, image_path: str = "data/pet_image.png"):
        super().__init__()
        self.image_path = image_path
        self._dragging = False
        self._drag_offset = QPoint()

        # 无边框 + 置顶 + 不在任务栏
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_ui()
        self.setMinimumSize(100, 150)

    def _setup_ui(self):
        """初始化 UI：加载图片或显示占位提示"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.image_label)

        self._load_image()

    def _load_image(self):
        """加载角色图片，若不存在则显示占位提示"""
        import os
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # 限制最大尺寸
                if pixmap.width() > 500 or pixmap.height() > 600:
                    pixmap = pixmap.scaled(
                        500, 600,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                self.image_label.setPixmap(pixmap)
                self.resize(pixmap.size())
                return

        # 无图片时显示占位提示
        self.image_label.setText(
            "🎨  请将动漫人物 PNG\n放入 data/pet_image.png"
        )
        self.image_label.setStyleSheet("""
            QLabel {
                color: rgba(180, 200, 230, 220);
                font-size: 16px;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                background: rgba(255, 255, 255, 60);
                border: 2px dashed rgba(180, 200, 230, 150);
                border-radius: 20px;
                padding: 30px;
            }
        """)
        self.resize(260, 160)

    def set_image(self, image_path: str):
        """更换角色图片"""
        self.image_path = image_path
        self._load_image()

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

    # ── 透明绘制 ──────────────────────────────────────

    def paintEvent(self, event):
        """只绘制子控件，背景完全透明"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 不填充背景，保持透明
