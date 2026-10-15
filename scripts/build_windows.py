"""Build with Python 3.12 x64 after installing requirements-windows.txt and PyInstaller."""

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()
    if sys.platform != "win32" or sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        raise SystemExit("Build with Windows x64 Python 3.12")
    sys.path.insert(0, str(ROOT))
    from src.ocr_detector import create_paddle_ocr_engine

    models = ROOT / "build" / "models"
    create_paddle_ocr_engine(lang="ch", model_dir=models)
    for name in ("det", "rec", "cls"):
        for file in ("inference.pdmodel", "inference.pdiparams"):
            if not (models / name / file).is_file():
                raise SystemExit(f"Missing model: {name}/{file}")

    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
         "--name", "AutoDouYin", "--distpath", str(ROOT / "dist"),
         "--workpath", str(ROOT / "build" / "pyinstaller"),
         "--specpath", str(ROOT / "build"),
         "--add-data", f"{ROOT / 'config.example.json'};.", str(ROOT / "launcher.py")],
        cwd=ROOT, check=True,
    )
    bundle = ROOT / "dist" / "AutoDouYin"
    internal = bundle / "_internal"
    runtime = internal / "runtime"
    runtime.mkdir(exist_ok=True)
    base = Path(sys.base_prefix)
    for path in base.iterdir():
        if path.is_file() and (path.suffix.lower() in (".exe", ".dll") or path.name == "LICENSE.txt"):
            shutil.copy2(path, runtime / path.name)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "site-packages", "test", "tests", "idlelib", "ensurepip")
    for folder in ("DLLs", "Lib"):
        shutil.copytree(base / folder, runtime / folder, ignore=ignore, dirs_exist_ok=True)

    packages = Path(sys.prefix) / "Lib" / "site-packages"
    destination = runtime / "Lib" / "site-packages"
    destination.mkdir(exist_ok=True)
    build_only = ("pip", "pyinstaller", "_pyinstaller", "altgraph", "pefile", "peutils", "pywin32_ctypes", "win32ctypes")
    for path in packages.iterdir():
        if path.name.lower().startswith(build_only) or path.name == "__pycache__":
            continue
        if path.is_dir():
            shutil.copytree(path, destination / path.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"), dirs_exist_ok=True)
        elif path.suffix != ".pyc":
            shutil.copy2(path, destination / path.name)
    (runtime / "python312._pth").write_text(".\nLib\nDLLs\nLib/site-packages\n../app\nimport site\n", encoding="utf-8")

    app_source = internal / "app" / "src"
    app_source.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "src").glob("*.py"):
        shutil.copy2(path, app_source / path.name)
    shutil.copytree(models, internal / "models", dirs_exist_ok=True)
    for name in ("README.md", "LICENSE", "config.example.json"):
        shutil.copy2(ROOT / name, bundle / name)
    versions = sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions(path=[str(destination)]) if d.metadata['Name'])
    (bundle / "runtime-versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")
    (bundle / "使用说明.txt").write_text(
        "AutoDouYin Windows 64 位免安装版\n\n"
        "1. 完整解压 ZIP，保留 AutoDouYin.exe 和 _internal 文件夹在一起。\n"
        "2. 双击 AutoDouYin.exe，打开 CS2 和浏览器，然后点击“开始”。\n"
        "3. 点击“打开配置”调整窗口标题和识别区域；修改后停止并重新开始。\n"
        "4. 点击“停止”或关闭启动器即可停止程序。\n\n"
        "不需要安装 Python。已内置 CPU OCR 依赖和中文识别模型。\n"
        "配置和日志位于 %LOCALAPPDATA%\\AutoDouYin，不会覆盖原有配置。\n"
        "程序异常时，可点击“查看日志”。请不要单独移动 exe 或从 ZIP 内直接运行。\n"
        "第三方依赖的许可证保留在 _internal/runtime/Lib/site-packages 的包元数据中；\n"
        "Python 许可证见 _internal/runtime/LICENSE.txt，PaddleOCR 模型采用 Apache-2.0。\n",
        encoding="utf-8-sig",
    )
    archive = ROOT / "dist" / f"AutoDouYin-v{args.version}-windows-x64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(bundle.parent))
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest}))


if __name__ == "__main__":
    main()
