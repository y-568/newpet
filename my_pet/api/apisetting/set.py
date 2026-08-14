from PySide6.QtWidgets import (QApplication, QWidget, QLineEdit, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
import json
import os
import requests

DEFN = "data/config/config.json"


# 异步校验线程
class ApiCheckThread(QThread):
    # 信号：(是否成功, 消息文本)
    result_signal = Signal(bool, str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key.strip()

    def run(self):
        if len(self.api_key) < 10:
            self.result_signal.emit(False, "密钥长度不足")
            return
        try:
            url = "https://api.deepseek.com/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                self.result_signal.emit(True, "密钥验证成功")
            elif resp.status_code == 401:
                self.result_signal.emit(False, "API Key无效或权限不足")
            else:
                self.result_signal.emit(False, f"服务器返回错误：{resp.status_code}")
        except requests.exceptions.Timeout:
            self.result_signal.emit(False, "请求超时，请检查网络")
        except Exception as e:
            self.result_signal.emit(False, f"网络异常：{str(e)}")


class ApiSettingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek API设置")
        self.resize(420, 180)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 标签 + 输入框一行
        line_layout = QHBoxLayout()
        label = QLabel("API Key：")
        label.setFixedWidth(70)
        self.api_edit = QLineEdit()
        self.api_edit.setPlaceholderText('请输入DeepSeek API Key')
        line_layout.addWidget(label)
        line_layout.addWidget(self.api_edit)

        # 确定、取消按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(line_layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        # 绑定按钮事件
        self.btn_ok.clicked.connect(self.on_confirm)
        self.btn_cancel.clicked.connect(self.on_cancel)

        self.check_thread = None  # 保存校验线程实例
        self.load_config()

    def load_config(self):
        """读取配置回显API Key"""
        if os.path.exists(DEFN):
            try:
                with open(DEFN, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    api_val = cfg.get("API_key", "").strip()
                    if api_val:
                        self.api_edit.setText(api_val)
            except Exception:
                pass

    def set_widget_enable(self, enable: bool):
        """批量启用/禁用控件"""
        self.btn_ok.setEnabled(enable)
        self.btn_cancel.setEnabled(enable)
        self.api_edit.setEnabled(enable)

    def on_confirm(self):
        api_key = self.api_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "输入错误", "API Key不能为空！")
            self.api_edit.setFocus()
            return

        # 禁用界面，开始校验
        self.set_widget_enable(False)
        self.check_thread = ApiCheckThread(api_key)
        self.check_thread.result_signal.connect(self.on_confirm_check_finish)
        self.check_thread.start()

    def on_confirm_check_finish(self, valid: bool, msg: str):
        self.set_widget_enable(True)
        if valid:
            # 保存配置
            os.makedirs(os.path.dirname(DEFN), exist_ok=True)
            cfg = {}
            if os.path.exists(DEFN):
                try:
                    with open(DEFN, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except:
                    pass
            cfg["API_key"] = self.api_edit.text().strip()
            with open(DEFN, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "成功", "DeepSeek API Key验证通过并保存！")
            self.close()
        else:
            QMessageBox.critical(self, "验证失败", msg)
            self.api_edit.setFocus()

    def verify_saved_api_async(self):
        """异步检查配置文件密钥（取消按钮调用）"""
        if not os.path.exists(DEFN):
            # 文件不存在
            res = QMessageBox.question(
                self,
                "警告",
                "配置文件不存在，暂无有效的DeepSeek API Key！\n关闭窗口可能导致程序无法运行，确定退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self.close()
            return

        try:
            with open(DEFN, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                saved_api = cfg.get("API_key", "").strip()
        except Exception:
            saved_api = ""

        if not saved_api:
            res = QMessageBox.question(
                self,
                "警告",
                "配置中未保存API Key！\n关闭窗口可能导致程序无法运行，确定退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self.close()
            return

        # 后台校验已保存的key
        self.set_widget_enable(False)
        self.check_thread = ApiCheckThread(saved_api)
        self.check_thread.result_signal.connect(self.on_cancel_check_finish)
        self.check_thread.start()

    def on_cancel_check_finish(self, valid: bool, msg: str):
        self.set_widget_enable(True)
        if valid:
            # 已有有效密钥，直接关闭
            self.close()
        else:
            res = QMessageBox.question(
                self,
                "警告",
                f"已保存的API校验失败：{msg}\n当前没有可用API，关闭窗口会影响程序运行，依然退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self.close()

    def on_cancel(self):
        """点击取消入口"""
        self.verify_saved_api_async()


if __name__ == '__main__':
    app = QApplication([])
    window = ApiSettingWindow()
    window.show()
    app.exec()