# AutoDouYin

一个用于 Windows 的 CS2 OCR 浏览器助手。通过识别游戏窗口中的观战提示，在进入观战状态时切换到指定浏览器并翻页；连续检测不到观战关键词后，切回 CS2。

## 功能

- 在可配置的窗口区域内识别文字，默认匹配“下一名玩家”或“切换”。
- 根据游戏窗口大小，按参考分辨率分别缩放 OCR 区域的横纵坐标。
- 使用连续帧确认和冷却时间减少重复触发，每次进入观战状态只执行一次浏览器操作。
- 支持向上/向下翻页和滚轮操作。
- 提供独立的 OCR 预览工具，可以输出识别结果和保存预处理截图。

## 下载启动器（无需安装 Python）

适用于 Windows 10/11 64 位。到 [GitHub Releases](https://github.com/tutoupifengxiaa/AutoDouYin/releases/latest) 下载 `AutoDouYin-v1.0.0-windows-x64.zip`。

1. 完整解压 ZIP，保留 `AutoDouYin.exe` 和 `_internal` 文件夹在一起。
2. 双击 `AutoDouYin.exe`，打开 CS2 和浏览器，点击“开始”。
3. 点击“打开配置”调整窗口标题、OCR 区域和关键词；保存后停止并重新开始。
4. 点击“停止”或关闭启动器即可停止程序；出现问题时点击“查看日志”。

启动器内置 Python、CPU 推理依赖和中文 OCR 模型，默认中文配置可直接离线加载。配置和日志保存在 `%LOCALAPPDATA%\AutoDouYin`，后续启动及更新程序时会保留已有配置。修改为其他 OCR 语言可能需要联网下载对应模型。

## 从源码安装

准备 Windows、Python 3.12，以及已经打开的 CS2 和目标浏览器窗口。在 PowerShell 中执行：

```powershell
git clone https://github.com/tutoupifengxiaa/AutoDouYin.git
cd AutoDouYin
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
Copy-Item config.example.json config.json
```

当前 OCR 适配使用 PaddleOCR 2.x 的结果格式，Windows 依赖版本见 `requirements-windows.txt`。程序使用 CPU 推理；OCR 的安装背景可参考 [PaddleOCR 2.x 官方说明](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version2.x/ppocr/quick_start.en.md)。从源码首次创建 OCR 引擎时可能需要联网下载模型。

## 配置和运行

编辑本地 `config.json`，使窗口标题、OCR 区域和关键词符合你的屏幕及游戏语言。`config.json` 不会提交到 GitHub；仓库仅提供 `config.example.json`。

| 配置项 | 含义 |
| --- | --- |
| `cs2_window_title` / `browser_window_title` | 用于查找游戏和浏览器窗口的标题子串 |
| `ocr_roi` | 相对于游戏窗口的识别区域，包含 `x`、`y`、`width`、`height` |
| `ocr_reference_width` / `ocr_reference_height` | 设置 OCR 区域时使用的参考窗口尺寸，默认 `1280 × 1024` |
| `ocr_lang` / `ocr_keywords` | OCR 语言和观战状态关键词，任一关键词匹配即可 |
| `poll_interval_ms` | 每轮检测后的等待时间 |
| `ocr_scale` / `threshold_value` | 图像放大倍数和二值化阈值 |
| `death_confirm_frames` / `alive_confirm_frames` | 确认进入/退出观战状态所需的连续帧数 |
| `action_cooldown_ms` | 两次浏览器操作之间的最短间隔 |
| `scroll_mode` | `page_down`、`page_up`、`scroll_down` 或 `scroll_up` |
| `scroll_amount` | 滚轮模式的滚动量；向下滚动通常使用负数 |
| `log_level` | 日志级别，默认 `INFO` |

先预览一次识别结果，确认区域和关键词正确：

```powershell
.\.venv\Scripts\python.exe -m src.roi_preview --once --save-path roi.png
```

预览工具支持 `--config` 指定配置文件；省略 `--once` 可持续检测。预览不会切换窗口或操作浏览器。

启动助手：

```powershell
.\.venv\Scripts\python.exe -c "from src.app import main; main()"
```

在终端按 `Ctrl+C` 停止。

也可以运行桌面启动器：

```powershell
.\.venv\Scripts\python.exe launcher.py
```

## 构建 Windows 免安装包

在 Windows x64、Python 3.12 环境中执行：

```powershell
py -3.12 -m venv build\venv
.\build\venv\Scripts\python.exe -m pip install -r requirements-windows.txt pyinstaller==6.16.0
.\build\venv\Scripts\python.exe scripts\build_windows.py --version 1.0.0
```

构建会下载中文模型，并在 `dist/` 生成 ZIP 和 SHA256 校验文件。运行包包含独立 Python 运行时、依赖及其许可证，实际依赖版本记录在包内的 `runtime-versions.txt`。GitHub 仓库保存源码，免安装包作为 Release 附件发布；项目的 `tests/` 和 `docs/` 不会打包或上传。

## 当前限制

- 截图读取桌面上的指定区域，游戏窗口被遮挡、最小化或移位后，识别结果可能受到影响，需要在实际窗口布局下校准。
- `focus_settle_ms` 是配置中的保留字段，当前实现尚未使用。
- 真实游戏画面、窗口布局和浏览器切换仍需在使用环境中校准。
- 本仓库发布源码和示例配置，测试文件与设计文档保留在本地。

## 许可证

本项目采用 [MIT License](LICENSE)。
