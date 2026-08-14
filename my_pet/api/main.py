"""
PetOverlay — 桌面 AI 宠物 Overlay（输出框 + 输入框）
作为主函数的子调用模块，只负责：
  - OutputWindow  (云朵回答框)    → 无边框 + 透明 + 可拖动，位于角色左侧
  - InputWindow   (用户输入框)    → 无边框 + 玻璃态 + 可拖动，位于角色下方
  - 齿轮菜单      (⚙️ 按钮)      → API设置 / 清空回答 / 退出
  - ESC 全局退出
角色图片窗口由外部函数负责，不在此模块管理。
"""
import sys
import json
import os

from PySide6.QtWidgets import (
    QApplication, QMenu, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QFont

try:
    from .minwindow.cloud_widget import CloudWidget
    from .minwindow.input_widget import InputOutputWidget
    from .apisetting.set import ApiSettingWindow
    from .core.api_worker import APIWorker
except ImportError:
    from minwindow.cloud_widget import CloudWidget
    from minwindow.input_widget import InputOutputWidget
    from apisetting.set import ApiSettingWindow
    from core.api_worker import APIWorker

# data/ 目录在 my_pet/data/ 下（而非相对 cwd）
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_API_FILE = os.path.join(_ROOT, "data", "config", "config.json")
CONFIG_POS_FILE = os.path.join(_ROOT, "data", "config", "dat.json")


class PetOverlayApp:
    """桌面宠物 Overlay — 输出窗口 + 输入窗口"""

    # overlay 窗口相对宠物的偏移量
    OUTPUT_GAP = 5    # 输出框与宠物的水平间距
    INPUT_GAP = 40    # 输入框与宠物的垂直间距
    PET_DEFAULT_HEIGHT = 150  # 宠物高度未知时的默认值

    def __init__(self, pet_window=None):
        self.api_key = ""
        self.api_worker = None
        self.pet_window = pet_window  # 宠物主窗口引用
        os.makedirs(os.path.dirname(CONFIG_API_FILE), exist_ok=True)

        # ── 两个无边框窗口 ──
        self.output_win = CloudWidget(standalone=True)
        self.input_win  = InputOutputWidget(standalone=True)

        self._load_api_key()
        self._register_shortcuts()
        self._connect_signals()

        self.output_win.show()
        self.input_win.show()
        self.input_win.input_box.setFocus()

        # 显示后再定位，确保窗口尺寸已正确计算
        self._setup_overlay_positions()
        # 延迟一次再定位，防止宠物图片尚未加载完成
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._update_overlay_positions)

    # ── 快捷键 ──────────────────────────────────────

    def _register_shortcuts(self):
        for win in (self.output_win, self.input_win):
            QShortcut(QKeySequence(Qt.Key_Escape), win).activated.connect(self._quit_app)

    # ── 齿轮菜单 ─────────────────────────────────────

    def _on_gear_clicked(self):
        """齿轮按钮 → 弹出菜单"""
        # 防止 GC：保存为实例属性
        self._gear_menu = QMenu()
        self._gear_menu.setStyleSheet("""
            QMenu {
                background: rgba(255, 255, 255, 235);
                border: 1px solid rgba(180, 200, 230, 200);
                border-radius: 8px;
                padding: 4px;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(150, 200, 255, 180);
            }
        """)

        self._gear_menu.addAction("⚙️  API 设置").triggered.connect(self._open_settings)
        self._gear_menu.addAction("🗑️  清空回答").triggered.connect(self._clear_output)
        self._gear_menu.addSeparator()
        self._gear_menu.addAction("✕  退出").triggered.connect(self._quit_app)

        # 在齿轮按钮下方弹出
        btn = self.input_win.btn_gear
        self._gear_menu.popup(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _clear_output(self):
        """清空输出窗口"""
        self.output_win.clear()

    # ── 位置：跟随宠物 ──────────────────────────────

    def _get_pet_position(self):
        """获取宠物当前位置 (x, y, width, height)"""
        if self.pet_window is not None:
            pw = self.pet_window.width()
            ph = self.pet_window.height()
            # 图片未加载时高度为 0，使用默认值避免输入框覆盖宠物
            if ph == 0:
                ph = self.PET_DEFAULT_HEIGHT
            return (self.pet_window.x(), self.pet_window.y(), pw, ph)
        # 无宠物引用时，从 dat.json 读取
        try:
            if os.path.exists(CONFIG_POS_FILE):
                with open(CONFIG_POS_FILE, "r", encoding="utf-8") as f:
                    pos = json.load(f).get("pet_window", {"x": 0, "y": 0})
                return (pos.get("x", 0), pos.get("y", 0), 150, 150)
        except Exception:
            pass
        return (0, 0, 150, 150)

    def _setup_overlay_positions(self):
        """根据宠物位置初始化 overlay 窗口位置，并绑定跟随信号"""
        self._update_overlay_positions()

        # 绑定宠物位置变化信号 → 实时跟随
        if self.pet_window is not None:
            self.pet_window.position_changed.connect(
                lambda x, y: self._update_overlay_positions()
            )

    def _update_overlay_positions(self):
        """根据宠物当前位置更新 output_window 和 input_window 的位置"""
        px, py, pw, ph = self._get_pet_position()

        # output_window：宠物左方，顶部对齐
        out_x = px - self.output_win.width() - self.OUTPUT_GAP
        out_y = py
        self.output_win.move(out_x, out_y)

        # input_window：宠物正下方，左侧对齐
        in_x = px
        in_y = py + ph + self.INPUT_GAP
        self.input_win.move(in_x, in_y)

    # ── API Key ─────────────────────────────────────

    def _load_api_key(self):
        try:
            if os.path.exists(CONFIG_API_FILE):
                with open(CONFIG_API_FILE, "r", encoding="utf-8") as f:
                    self.api_key = json.load(f).get("API_key", "").strip()
        except Exception:
            self.api_key = ""

    def _open_settings(self):
        dlg = ApiSettingWindow()
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setAttribute(Qt.WA_DeleteOnClose)
        dlg.destroyed.connect(lambda: self._load_api_key())
        dlg.show()

    # ── 信号 ────────────────────────────────────────

    def _connect_signals(self):
        self.input_win.send_message.connect(self._on_send_message)
        self.input_win.gear_clicked.connect(self._on_gear_clicked)

    # ── API 调用 ────────────────────────────────────

    def _on_send_message(self, message: str):
        if not message.strip():
            return
        self._load_api_key()
        if not self.api_key:
            QMessageBox.warning(self.input_win, "缺少 API Key",
                                "请在 ⚙️ 菜单中设置 DeepSeek API Key！")
            self._open_settings()
            return

        self.output_win.set_text("🤔 思考中...")
        self.input_win.set_status("正在请求 DeepSeek...")
        self.input_win.set_enabled(False)

        if self.api_worker and self.api_worker.isRunning():
            self.api_worker.terminate()
            self.api_worker.wait()

        self.api_worker = APIWorker(self.api_key, message)
        self.api_worker.progress.connect(self._on_stream_progress)
        self.api_worker.finished.connect(self._on_response_finished)
        self.api_worker.error.connect(self._on_response_error)
        self.api_worker.start()

    def _on_stream_progress(self, text: str):
        self.output_win.set_text(text)

    def _on_response_finished(self, text: str):
        self.output_win.set_text(text)
        self.input_win.clear_status()
        self.input_win.set_enabled(True)

    def _on_response_error(self, error_msg: str):
        self.output_win.set_text(f"❌ {error_msg}")
        self.input_win.set_status(f"错误: {error_msg}")
        self.input_win.set_enabled(True)

    # ── 退出 ────────────────────────────────────────

    def _quit_app(self):
        # 宠物位置已由 pet_window 的 moveEvent 实时保存，无需额外处理
        QApplication.quit()


# ==================== 入口 ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setQuitOnLastWindowClosed(False)
    pet = PetOverlayApp()
    sys.exit(app.exec())
