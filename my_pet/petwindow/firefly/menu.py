from qfluentwidgets import (
    Action,
    FluentIcon,
    RoundMenu,
    MenuAnimationType
)
from PySide6.QtGui import QActionGroup

try:
    from ...api.main import PetOverlayApp
except ImportError:
    from api.main import PetOverlayApp


class Menu:
    def __init__(self, parent=None):
        self.parent = parent

        self.API = Action(
            FluentIcon.APPLICATION, "聊天",
            triggered=self._open_pet_overlay
        )

        self.freeWalk = Action(
            FluentIcon.APPLICATION, "游动",
            triggered=lambda: self.parent.setFreeWalking()
        )
        self.bgingAction = Action(
            FluentIcon.APPLICATION, "变身",
            triggered=lambda: self.parent.actionEventQThread.bg()
        )
        self.angrypAction = Action(
            FluentIcon.APPLICATION, "生气",
            triggered=lambda: self.parent.actionEventQThread.angry()
        )
        self.feedingAction = Action(
            FluentIcon.APPLICATION, "喂食",
            triggered=lambda: self.parent.actionEventQThread.eat()
        )
        self.sleepAction = Action(
            FluentIcon.APPLICATION, "睡觉",
            triggered=lambda: self.parent.actionEventQThread.sleep()
        )
        self.exitAction = Action(
            FluentIcon.EMBED, "退出",
            triggered=lambda: self.parent.close()
        )

    def _open_pet_overlay(self):
        """启动 AI 宠物聊天覆盖层"""
        self._pet_app = PetOverlayApp(pet_window=self.parent)

    def contextMenuEvent(self, e):
        self.menu = RoundMenu()
        self.menu.addActions([self.API])
        self.menu.addSeparator()
        self.menu.addActions([
            self.freeWalk,
            self.bgingAction,
            self.angrypAction,
            self.feedingAction,
            self.sleepAction,
        ])
        self.menu.addSeparator()
        self.menu.addAction(self.exitAction)

        self.menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)
