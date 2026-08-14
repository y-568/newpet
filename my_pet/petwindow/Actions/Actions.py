import os
import json
from typing import Any
from PySide6.QtCore import Signal, QThread
from loguru import logger


class ActionPic:
    """动作图片加载器"""

    def __init__(self) -> None:
        # data/ 目录在 my_pet/data/ 下
        _here = os.path.dirname(os.path.abspath(__file__))
        self._root = os.path.normpath(os.path.join(_here, "..", ".."))
        self.path = os.path.join(self._root, "data", "config", "action_pictures.json")
        if not os.path.isfile(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w+", encoding="utf-8") as f:
                f.write("{}")
        self.actions = []
        self._missing_keys = set()
        self._bad_paths = set()

    def read(self, key: str) -> list:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())
                item = data.get(key)
                if not item:
                    if key not in self._missing_keys:
                        self._missing_keys.add(key)
                        logger.warning(f"未找到动作配置: {key}（请检查 action_pictures.json）")
                    return None

                path = item.get("path")
                ext = item.get("type", ".png")
                if not path:
                    if key not in self._missing_keys:
                        self._missing_keys.add(key)
                        logger.error(f"{key} 缺少 path 字段")
                    return None

                # 相对路径 → 补全到 my_pet/data/ 下
                if not os.path.isabs(path):
                    path = os.path.join(self._root, path)

                if not os.path.exists(path):
                    if path not in self._bad_paths:
                        self._bad_paths.add(path)
                        logger.error(f"路径不存在: {path}")
                    return None

                exts = [e.strip() for e in ext.split(",")]
                self.actions = []
                for root, _, files in os.walk(path):
                    for file in files:
                        if any(file.lower().endswith(e.lower()) for e in exts):
                            self.actions.append(os.path.join(root, file))
                if not self.actions:
                    logger.warning(f"{path}下无{ext}文件")
                return self.actions
        except Exception as e:
            logger.error(f"读取失败: {e}")
            return None


loader = ActionPic()
CONTINUOUS = ["Standby", "mention", "sleep", "discomfort"]
NON_CONTINUOUS = ["left", "right", "eat", "love", "angry", "bg", "Lovely"]

actions = {}
for key in CONTINUOUS + NON_CONTINUOUS:
    actions[key] = loader.read(key)


class ActionEvent(QThread):
    """动作事件线程"""

    result = Signal(str)
    startTimer = Signal()
    stopTimer = Signal()
    gifStarted = Signal(str)   # 发送 GIF 文件路径
    gifFinished = Signal()     # GIF 播放完成

    def __init__(self, callback: Any) -> None:
        super().__init__()
        self.callback = callback
        self.interrupted = False
        self.sign = "Standby"
        self.pics = actions.get(self.sign, []) or []
        self._is_gif = False

    @property
    def is_gif(self) -> bool:
        """当前动作是否使用 GIF 资源"""
        return self._is_gif

    def run(self) -> None:
        self.startTimer.emit()

    def play(self) -> None:
        if self.interrupted:
            return

        if not self.pics:
            actions[self.sign] = loader.read(self.sign)
            self.pics = actions.get(self.sign, []) or []
            self.result.emit(self.sign)
            return

        img = self.pics.pop(0)
        self.callback(img)

        if self.sign in CONTINUOUS:
            self.pics.append(img)
        elif self.sign in ['left', 'right']:
            self.result.emit(self.sign)

    def load(self, key: str) -> None:
        self.sign = key
        self.pics = actions.get(key, []) or []
        # 检测是否为 GIF 动画
        self._is_gif = bool(self.pics) and self.pics[0].lower().endswith('.gif')
        if self._is_gif and self.pics:
            self.gifStarted.emit(self.pics[0])

    def mention(self) -> None:
        self.load("mention")

    def standby(self) -> None:
        self.load("Standby")

    def eat(self) -> None:
        self.load("eat")

    def sleep(self) -> None:
        self.load("sleep")

    def love(self) -> None:
        self.load("love")

    def left(self) -> None:
        self.load("left")

    def right(self) -> None:
        self.load("right")

    def angry(self) -> None:
        self.load("angry")

    def bg(self) -> None:
        self.load("bg")

    