import random
import json
from typing import *

from loguru import logger
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QLabel
)
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtWidgets import QApplication


import sys as _sys, os as _os
try:
    from ..Actions.Actions import ActionEvent
    from .menu import Menu
except ImportError:
    _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    _sys.path.insert(0, _root)
    from petwindow.Actions.Actions import ActionEvent
    from petwindow.firefly.menu import Menu

# dat.json 配置文件路径（my_pet/data/config/dat.json）
CONFIG_POS_FILE = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "data", "config", "dat.json"
)

class MainWindow(QMainWindow):
    startActionEventTimerSignal = Signal()
    stopActionEventTimerSignal = Signal()
    position_changed = Signal(int, int)  # 宠物位置变化信号 (x, y)
    def __init__(self,app:QApplication)->None:
        super().__init__()
        self.app=app
        self.isFreeWalking=False
        self.walkingDirection=random.choice(["left","right"])
        self.scaling = 0  # 缩放比例，0=不缩放
        self.currentBgImage = ""
        self._loading_position = False  # 防止加载位置时触发保存

        self.actionEventQThread = ActionEvent(self.switchBackground)
        self.actionEventQThread.result.connect(self.ActionEventMethod)
        self.actionEventQThread.startTimer.connect(self.startTimer)
        self.actionEventQThread.stopTimer.connect(self.stopTimer)
        self.actionEventQThread.start()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("MyFlowingFireflyWife")

        self.label = QLabel(self)

        self.RightClickMenu = Menu(self)

        # 加载宠物位置（默认左上角 0,0）
        self._load_pet_position()

    def closeEvent(self, event):
        """关闭窗口时清理线程"""
        self.actionEventQThread.interrupted = True
        self.actionEventQThread.quit()
        self.actionEventQThread.wait(1000)
        super().closeEvent(event)

    def moveEvent(self, event):
        """窗口移动时保存位置并发出信号"""
        super().moveEvent(event)
        if not self._loading_position:
            self._save_pet_position()
            self.position_changed.emit(self.x(), self.y())

    def _load_pet_position(self):
        """从 dat.json 加载宠物位置（默认右上角）"""
        self._loading_position = True
        try:
            screen = self.app.primaryScreen().availableGeometry()
            default_x = screen.right()  # 右上角 x，后续由 _clamp_to_screen 修正
            default_y = screen.y()      # 屏幕顶部
            if _os.path.exists(CONFIG_POS_FILE):
                with open(CONFIG_POS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pos = data.get("pet_window", {"x": default_x, "y": default_y})
                self.move(pos.get("x", default_x), pos.get("y", default_y))
            else:
                self.move(default_x, default_y)
        except Exception as e:
            logger.warning(f"加载宠物位置失败: {e}")
            self.move(0, 0)
        finally:
            self._loading_position = False

    def _save_pet_position(self):
        """保存宠物位置到 dat.json（保留其他字段）"""
        try:
            data = {}
            if _os.path.exists(CONFIG_POS_FILE):
                with open(CONFIG_POS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["pet_window"] = {"x": self.x(), "y": self.y()}
            _os.makedirs(_os.path.dirname(CONFIG_POS_FILE), exist_ok=True)
            with open(CONFIG_POS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存宠物位置失败: {e}")

    def contextMenuEvent(self, event):
        return self.RightClickMenu.contextMenuEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """重写 mouseMoveEvent 以实现窗口拖动"""
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            event.accept()
        return super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        重写 mousePressEvent
        :return None
        """
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            event.accept()
            # 界面上半部分为摸头触发区
            trigger_height = self.height() / 4  # 触发区高度占窗口一半
            trigger_area = QRect(0, 0, self.width(), int(trigger_height))

            # 检查点击是否在摸头触发区域内
            if trigger_area.contains(event.pos()):
                self.actionEventQThread.love()  # 执行摸头动作
            else:
                # 切换提起动作
                self.actionEventQThread.mention()
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        重写鼠标释放
        :return None
        """
        if event.button() == Qt.LeftButton:
            event.accept()
            # 释放mention action, 重启 standbyAction
            self.actionEventQThread.standby()
            self.isFreeWalking = False
        return super().mouseReleaseEvent(event)

    def switchBackground(self, filePath: str) -> None:
        """
        根据`filePath`值，切换背景图片
        :param filePath: str | 文件路径
        """
        pixmap = QPixmap(filePath)
        if self.scaling > 0:
            pixmap = pixmap.scaled(
                pixmap.width() // self.scaling,
                pixmap.height() // self.scaling,
                Qt.KeepAspectRatio
            )
        
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.size())
        self.resize(pixmap.size())
        self._clamp_to_screen()
        self.currentBgImage = filePath

    def _clamp_to_screen(self):
        """确保窗口不超出屏幕边界"""
        screen = self.app.primaryScreen().availableGeometry()
        x = max(screen.x(), min(self.x(), screen.right() - self.width()))
        y = max(screen.y(), min(self.y(), screen.bottom() - self.height()))
        if x != self.x() or y != self.y():
            self.move(x, y)

    def ActionEventMethod(self, result: str) -> None:
        """
        动作事件的返回方法
        :param result: bool | 判断是否正常结束
        """
        if not result:
            return None
        if result != "Standby" and self.isFreeWalking is False:
            self.actionEventQThread.standby()

        if self.isFreeWalking is True:
            self.actionEventQThread.load(self.walkingDirection)
            if self.walkingDirection == "left":
                moveFunc = self.FireflyMove("left")
            elif self.walkingDirection == "right":
                moveFunc = self.FireflyMove("right")
            moveFunc(self)
            # 检查是否到达屏幕边缘并改变方向
            if self.isFreeWalking:
                screen_geometry = self.app.primaryScreen().geometry()
                if (self.walkingDirection == "left" and self.x() <= screen_geometry.x()) or \
                   (self.walkingDirection == "right" and self.x() + self.width() >= screen_geometry.right()):
                    self.walkingDirection = "right" if self.walkingDirection == "left" else "left"
                    logger.info(f"Reached screen edge, turning to {self.walkingDirection}")
            
    def setFreeWalking(self) -> None:
        """设置为自由行动状态"""
        logger.info(f"If free walking: {self.isFreeWalking}")
        self.isFreeWalking = not self.isFreeWalking
        self.actionEventQThread.load(self.walkingDirection)

    def FireflyMove(self, direction: str) -> callable:
        """
        向指定方向移动`左右`
        :param direction: str | 方向， left or right
        :return callable~
        """
        def left(self):
            x = self.x()
            # 窗口向左移动，直到撞到屏幕左边界
            if x > 0:
                self.move(x - 15, self.y())

        def right(self):
            # 获取当前窗口位置和屏幕的尺寸
            x = self.x()
            screen = QApplication.primaryScreen().geometry()
            # 窗口向右移动，直到撞到屏幕右边界
            if x + self.width() < screen.width():
                self.move(x + 15, self.y())
        return left if direction == "left" else right

    def startTimer(self) -> None:
        """启动执行动作的定时器"""
        if not hasattr(self, 'action_timer'):
            self.action_timer = QTimer(self)
            self.action_timer.timeout.connect(self.actionEventQThread.play)
        self.action_timer.start(200)

    def stopTimer(self) -> None:
        """停止执行动作的定时器"""
        if hasattr(self, 'action_timer'):
            self.action_timer.stop()

    def updateConfig(self) -> None:
        """更新当前窗口的配置"""
        try:
            from firefly.fireflywindowconfig import ConfigFile
            self.mainConfigFileObject = ConfigFile()
            self.mainConfigFileObject.data = self.mainConfigFileObject.read()
            self.scaling = self.mainConfigFileObject.data.get("scaling", 0)
            self.isPlayVoiceOnStart = self.mainConfigFileObject.data.get("is_play_VoiceOnStart", True)
            self.isPlayVoiceOnClose = self.mainConfigFileObject.data.get("is_play_VoiceOnClose", True)
        except ImportError:
            logger.warning("ConfigFile not found, using defaults")
            self.scaling = 0
        

