"""Windows desktop entry point; OCR runs in an isolated child process."""

import argparse
import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def data_directory() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "AutoDouYin"


def ensure_config(directory: Path, sample: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "config.json"
    if not target.exists():
        contents = sample.read_text(encoding="utf-8")
        try:
            with target.open("x", encoding="utf-8") as output:
                output.write(contents)
        except FileExistsError:
            pass
    return target


def worker_command(config: Path, report: Path | None = None) -> list[str]:
    root = resource_root()
    executable = root / "runtime" / "python.exe" if getattr(sys, "frozen", False) else Path(sys.executable)
    command = [str(executable), "-B", "-m", "src.desktop_worker", "--config", str(config.resolve())]
    models = root / "models"
    if models.is_dir() or getattr(sys, "frozen", False):
        command.extend(["--models", str(models)])
    if report is not None:
        command.extend(["--self-test", str(report.resolve())])
    return command


class Launcher:
    def __init__(self, root: tk.Tk, config: Path) -> None:
        self.root = root
        self.config = config
        self.process: subprocess.Popen | None = None
        self.log_file = None
        self.stop_requested_at: float | None = None
        self.closing = False
        root.title("AutoDouYin 启动器")
        root.geometry("540x260")
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="AutoDouYin · CS2 浏览器助手", font=("Microsoft YaHei UI", 15)).pack(anchor="w")
        ttk.Label(frame, text="先打开 CS2 和浏览器，再点击开始。\n修改配置后，停止并重新开始即可生效。", padding=(0, 12)).pack(anchor="w")
        self.status = tk.StringVar(value="已就绪")
        ttk.Label(frame, textvariable=self.status, wraplength=490).pack(anchor="w", pady=(0, 12))
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w")
        self.start_button = ttk.Button(buttons, text="开始", command=self.start)
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = ttk.Button(buttons, text="停止", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="打开配置", command=lambda: self.open_file(self.config)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="查看日志", command=lambda: self.open_file(self.config.parent / "app.log")).pack(side="left")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(200, self.poll)

    def open_file(self, path: Path) -> None:
        try:
            os.startfile(path)
        except OSError as error:
            messagebox.showerror("无法打开文件", str(error), parent=self.root)

    def start(self) -> None:
        if self.process is not None:
            return
        try:
            self.log_file = (self.config.parent / "app.log").open("a", encoding="utf-8")
            self.log_file.write("\n--- AutoDouYin started ---\n")
            self.log_file.flush()
            self.process = subprocess.Popen(
                worker_command(self.config),
                cwd=resource_root(),
                stdin=subprocess.PIPE,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (OSError, ValueError) as error:
            if self.log_file is not None:
                self.log_file.close()
                self.log_file = None
            messagebox.showerror("启动失败", str(error), parent=self.root)
            return
        self.stop_requested_at = None
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("运行中；模型载入时请稍候。可在日志中查看识别结果。")

    def stop(self) -> None:
        if self.process is None or self.stop_requested_at is not None:
            return
        self.stop_requested_at = time.monotonic()
        self.stop_button.configure(state="disabled")
        self.status.set("正在停止…")
        try:
            self.process.stdin.write("stop\n")
            self.process.stdin.flush()
        except (OSError, ValueError):
            pass

    def poll(self) -> None:
        if self.process is not None:
            code = self.process.poll()
            if code is None and self.stop_requested_at is not None and time.monotonic() - self.stop_requested_at > 5:
                self.process.terminate()
            elif code is not None:
                self.process.stdin.close()
                self.process = None
                self.log_file.close()
                self.log_file = None
                requested = self.stop_requested_at is not None
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.status.set("已停止" if code == 0 or requested else "程序异常退出，请点击“查看日志”查看原因。")
        if self.closing and self.process is None:
            self.root.destroy()
            return
        self.root.after(200, self.poll)

    def close(self) -> None:
        self.closing = True
        self.start_button.configure(state="disabled")
        self.stop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    try:
        if args.self_test is not None:
            root.update()
            config = ensure_config(args.self_test.resolve().parent / "settings", resource_root() / "config.example.json")
            with args.self_test.with_suffix(".log").open("w", encoding="utf-8") as output:
                result = subprocess.run(
                    worker_command(config, args.self_test), cwd=resource_root(),
                    stdout=output, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            return result.returncode
        config = ensure_config(data_directory(), resource_root() / "config.example.json")
        Launcher(root, config)
        root.deiconify()
        root.mainloop()
        return 0
    except Exception as error:
        messagebox.showerror("AutoDouYin 启动失败", str(error), parent=root)
        return 1
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
