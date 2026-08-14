# newpet 🦋

一个基于 **PySide6** 的桌面小宠物（流萤 Firefly），支持接入 **DeepSeek API** 进行 AI 聊天。

> 💡 本项目代码参考/学习自 [PYmili/MyFlowingFireflyWife](https://github.com/PYmili/MyFlowingFireflyWife)，仅供学习交流使用。

## ✨ 功能特性

- 🐱 **桌面宠物**：无边框、透明背景、置顶显示的桌面小宠物，可自由拖动，位置自动记忆。
- 🚶 **自由游动**：宠物可在屏幕内左右游动，碰到边缘自动掉头。
- 🎬 **丰富动作**：待机、摸头、提起、喂食、睡觉、生气、变身等多种交互动作（支持 PNG 帧动画与 GIF）。
- 🖱️ **右键菜单**：基于 `qfluentwidgets` 的圆角菜单，一键切换动作 / 打开聊天 / 退出。
- 💬 **AI 聊天**：接入 DeepSeek API，流式输出；带云朵回答框 + 玻璃态输入框，回答框/输入框会跟随宠物移动。
- ⚙️ **API 设置**：齿轮菜单内可视化设置 API Key，也可直接编辑配置文件。

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Windows（本项目在 Windows 11 上开发测试）

### 1. 安装依赖

```bash
pip install PySide6 openai loguru qfluentwidgets
```

### 2. 配置 DeepSeek API Key

两种方式任选其一：

- **方式一（推荐）**：运行程序后，在输入框的 ⚙️ 菜单中选择「API 设置」填入 Key。
- **方式二**：直接编辑 [`my_pet/data/config/config.json`](my_pet/data/config/config.json)：

```json
{
    "API_key": "你的 DeepSeek API Key"
}
```

> API Key 可前往 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取。

### 3. 运行

```bash
python my_pet/mainpet.py
```

## 🎮 使用说明

| 操作 | 说明 |
| --- | --- |
| 左键拖动宠物 | 移动宠物位置（位置会自动保存） |
| 点击宠物上半部分 | 摸头互动 |
| 点击宠物下半部分 | 提起互动 |
| 右键宠物 | 打开菜单（聊天 / 游动 / 变身 / 生气 / 喂食 / 睡觉 / 退出） |
| 「聊天」 | 打开 AI 聊天输入框与云朵回答框 |
| ⚙️ 菜单 | API 设置 / 清空回答 / 退出 |
| `Esc` | 退出聊天覆盖层 |

## 📁 项目结构

```
newpet/
├── my_pet/
│   ├── mainpet.py                    # 程序入口
│   ├── petwindow/
│   │   ├── Actions/Actions.py        # 动作事件线程（帧动画 / GIF）
│   │   └── firefly/                  # 宠物主窗口、右键菜单
│   ├── api/
│   │   ├── main.py                   # AI 聊天覆盖层（输出框 + 输入框）
│   │   ├── core/api_worker.py        # DeepSeek API 调用线程（流式）
│   │   ├── apisetting/set.py         # API 设置窗口
│   │   └── minwindow/                # 云朵回答框 / 输入框控件
│   └── data/
│       ├── assets/                   # 动作图片、GIF、背景、音频素材
│       └── config/                   # 配置文件（API Key、动作图片路径、位置）
├── README.md
└── LICENSE
```

## 🙏 参考与致谢

- 本项目代码参考/学习自 [PYmili/MyFlowingFireflyWife](https://github.com/PYmili/MyFlowingFireflyWife)，特此致谢。
- 角色形象「流萤（Firefly）」及音频、图片素材版权归原作者及米哈游《崩坏：星穹铁道》所有。

## ⚠️ 版权声明

本项目**仅供学习交流使用**，请勿用于商业用途。

如涉及任何版权或侵权问题，请联系作者，我们将在第一时间下架、删除相关内容。
