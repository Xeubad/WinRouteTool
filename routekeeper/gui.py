"""GUI 界面模块"""

import ctypes
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

try:
    from routekeeper import route_manager, storage
except ImportError:
    from . import route_manager, storage


class RouteKeeperGUI:
    """RouteKeeper GUI 主窗口"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RouteKeeper - Windows 静态路由管理工具")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        # 检查管理员权限
        if not self._check_admin():
            messagebox.showerror("权限错误", "此程序需要管理员权限运行\n请以管理员身份运行")
            root.destroy()
            return

        # 创建界面
        self._create_widgets()

        # 加载路由
        self.refresh_routes()

    def _check_admin(self) -> bool:
        """检查管理员权限"""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except AttributeError:
            return True

    def _create_widgets(self) -> None:
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="刷新", command=self.refresh_routes).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="添加路由", command=self.add_route_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="复制全部", command=self.copy_all).pack(side=tk.LEFT, padx=5)

        # 路由列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建 Treeview
        columns = ("destination", "mask", "gateway", "metric", "persistent")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")

        # 定义列
        self.tree.heading("destination", text="目的网络")
        self.tree.heading("mask", text="子网掩码")
        self.tree.heading("gateway", text="网关")
        self.tree.heading("metric", text="跃点数")
        self.tree.heading("persistent", text="持久化")

        # 设置列宽
        self.tree.column("destination", width=150)
        self.tree.column("mask", width=150)
        self.tree.column("gateway", width=150)
        self.tree.column("metric", width=80, anchor=tk.CENTER)
        self.tree.column("persistent", width=80, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制选中行", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制所有路由", command=self.copy_all)

        # 绑定事件
        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # 右键菜单
        self.tree.bind("<Control-c>", lambda e: self.copy_selected())  # Ctrl+C 复制
        self.tree.bind("<Control-C>", lambda e: self.copy_selected())  # Ctrl+C 复制

    def refresh_routes(self) -> None:
        """刷新路由列表"""
        try:
            # 清空列表
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 获取路由
            routes = route_manager.list_routes()

            # 添加到列表
            for route in sorted(routes, key=lambda r: r.destination):
                self.tree.insert("", tk.END, values=(
                    route.destination,
                    route.mask,
                    route.gateway,
                    route.metric,
                    "✓" if route.is_persistent else "",
                ))

            self.status_var.set(f"共 {len(routes)} 条路由")

        except Exception as e:
            messagebox.showerror("错误", f"获取路由失败: {e}")
            self.status_var.set("获取路由失败")

    def add_route_dialog(self) -> None:
        """显示添加路由对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加路由")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.geometry(f"+{self.root.winfo_x() + 250}+{self.root.winfo_y() + 175}")

        # 表单
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 目的网络
        ttk.Label(form_frame, text="目的网络 (CIDR):").grid(row=0, column=0, sticky=tk.W, pady=5)
        dest_entry = ttk.Entry(form_frame, width=30)
        dest_entry.grid(row=0, column=1, pady=5)
        dest_entry.insert(0, "10.10.0.0/16")

        # 网关
        ttk.Label(form_frame, text="网关:").grid(row=1, column=0, sticky=tk.W, pady=5)
        gateway_entry = ttk.Entry(form_frame, width=30)
        gateway_entry.grid(row=1, column=1, pady=5)
        gateway_entry.insert(0, "192.168.1.1")

        # 跃点数
        ttk.Label(form_frame, text="跃点数 (留空=自动):").grid(row=2, column=0, sticky=tk.W, pady=5)
        metric_entry = ttk.Entry(form_frame, width=30)
        metric_entry.grid(row=2, column=1, pady=5)

        # 持久化
        persistent_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="持久化保存", variable=persistent_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        def on_add():
            """添加路由"""
            cidr = dest_entry.get().strip()
            gateway = gateway_entry.get().strip()
            metric_str = metric_entry.get().strip()
            persistent = persistent_var.get()

            # 验证输入
            if not cidr:
                messagebox.showwarning("警告", "请输入目的网络")
                return

            if not gateway:
                messagebox.showwarning("警告", "请输入网关")
                return

            try:
                if metric_str:
                    metric = int(metric_str)
                    if metric < 0:
                        raise ValueError
                else:
                    metric = 0  # 留空表示由 Windows 自动分配
            except ValueError:
                messagebox.showwarning("警告", "跃点数必须是非负整数（或留空自动分配）")
                return

            # 添加路由
            try:
                route_manager.add_route(cidr, gateway, metric, persistent)
                messagebox.showinfo("成功", f"路由 {cidr} 添加成功")
                dialog.destroy()
                self.refresh_routes()
            except Exception as e:
                messagebox.showerror("错误", f"添加路由失败: {e}")

        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="添加", command=on_add).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def delete_selected(self) -> None:
        """删除选中的路由"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的路由")
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        destination = values[0]
        mask = values[1]

        cidr = f"{destination}/{route_manager.win_api.mask_to_cidr(mask)}"

        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除路由 {cidr} 吗？"):
            return

        # 删除路由
        try:
            route_manager.delete_route(cidr)
            messagebox.showinfo("成功", f"路由 {cidr} 删除成功")
            self.refresh_routes()
        except Exception as e:
            messagebox.showerror("错误", f"删除路由失败: {e}")

    def on_item_double_click(self, event: tk.Event) -> None:
        """双击路由项"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            values = item["values"]
            messagebox.showinfo(
                "路由详情",
                f"目的网络: {values[0]}\n"
                f"子网掩码: {values[1]}\n"
                f"网关: {values[2]}\n"
                f"跃点数: {values[3]}\n"
                f"持久化: {values[4] if values[4] else '否'}"
            )

    def show_context_menu(self, event: tk.Event) -> None:
        """显示右键菜单"""
        # 选中右键点击的行
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)

    def copy_selected(self) -> None:
        """复制选中的路由到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要复制的路由")
            return

        # 构建复制内容
        lines = ["目的网络\t子网掩码\t网关\t跃点数\t持久化"]
        for item_id in selected:
            values = self.tree.item(item_id)["values"]
            line = f"{values[0]}\t{values[1]}\t{values[2]}\t{values[3]}\t{values[4] if values[4] else ''}"
            lines.append(line)

        content = "\n".join(lines)

        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()

        self.status_var.set(f"已复制 {len(selected)} 条路由到剪贴板")

    def copy_all(self) -> None:
        """复制所有路由到剪贴板"""
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("提示", "没有路由可复制")
            return

        # 构建复制内容
        lines = ["目的网络\t子网掩码\t网关\t跃点数\t持久化"]
        for item_id in children:
            values = self.tree.item(item_id)["values"]
            line = f"{values[0]}\t{values[1]}\t{values[2]}\t{values[3]}\t{values[4] if values[4] else ''}"
            lines.append(line)

        content = "\n".join(lines)

        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()

        self.status_var.set(f"已复制所有 {len(children)} 条路由到剪贴板")


def main():
    """启动 GUI"""
    root = tk.Tk()
    app = RouteKeeperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
