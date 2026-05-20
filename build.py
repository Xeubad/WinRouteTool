"""打包脚本 - 将 RouteKeeper 打包为 exe"""

import subprocess
import sys
from pathlib import Path


def build():
    """执行打包"""
    project_dir = Path(__file__).parent

    # PyInstaller 参数
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "RouteKeeper",
        "--onefile",                    # 单文件
        "--windowed",                   # GUI 模式，不显示控制台
        "--clean",                      # 清理缓存
        "--noconfirm",                  # 不询问确认
        "--distpath", str(project_dir / "dist"),
        "--workpath", str(project_dir / "build"),
        "--specpath", str(project_dir),
        str(project_dir / "routekeeper" / "__main__.py"),
    ]

    print("开始打包 RouteKeeper...")
    print(f"命令: {' '.join(args)}")

    result = subprocess.run(args, cwd=project_dir)

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "RouteKeeper.exe"
        print(f"\n打包成功!")
        print(f"输出文件: {exe_path}")
        print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"\n打包失败，退出码: {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
