"""允许通过 python -m routekeeper 运行或直接运行打包后的 exe"""

import sys
import os

# 将当前目录添加到 Python 路径，支持打包后的 exe 运行
if getattr(sys, 'frozen', False):
    # 打包后的 exe 运行
    app_dir = os.path.dirname(sys.executable)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
else:
    # 普通 Python 运行
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

# 尝试导入，支持相对导入和绝对导入
try:
    from routekeeper import cli, gui
except ImportError:
    from . import cli, gui

def main():
    """主入口：无参数时启动 GUI，有参数时使用 CLI"""
    if len(sys.argv) <= 1:
        # 双击 exe 无参数，启动 GUI
        try:
            gui.main()
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", f"启动 GUI 失败: {e}")
    else:
        # 有参数，使用 CLI
        cli.main()

if __name__ == "__main__":
    main()
