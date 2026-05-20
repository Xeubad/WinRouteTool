#!/usr/bin/env python3
"""
RouteKeeper 使用示例

此脚本演示如何通过 Python API 使用 RouteKeeper。
注意：需要管理员权限运行。
"""

import sys
import os

# 添加父目录到路径，以便导入 routekeeper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routekeeper import route_manager
from routekeeper import storage


def demo_list_routes():
    """演示：列出所有路由"""
    print("\n=== 列出所有路由 ===\n")

    routes = route_manager.list_routes()
    for route in routes:
        cidr = route_manager.to_cidr(route.destination, route.mask)
        print(f"  {cidr} -> {route.gateway} (metric: {route.metric})")


def demo_add_route():
    """演示：添加路由"""
    print("\n=== 添加路由 ===\n")

    try:
        # 添加一条测试路由
        route = route_manager.add_route(
            cidr="10.10.0.0/16",
            gateway="192.168.1.1",
            metric=10,
            persistent=True,
        )
        print(f"  成功添加: {route.destination}/{route_manager.win_api.mask_to_cidr(route.mask)}")
        print(f"  网关: {route.gateway}")
        print(f"  跃点数: {route.metric}")
    except Exception as e:
        print(f"  添加失败: {e}")


def demo_delete_route():
    """演示：删除路由"""
    print("\n=== 删除路由 ===\n")

    try:
        route_manager.delete_route("10.10.0.0/16")
        print("  成功删除: 10.10.0.0/16")
    except Exception as e:
        print(f"  删除失败: {e}")


def demo_storage():
    """演示：查看存储信息"""
    print("\n=== 存储信息 ===\n")

    try:
        path = storage.get_storage_path()
        print(f"  存储路径: {path}")

        if path.exists():
            data = storage.load_routes()
            print(f"  版本: {data.get('version', '未知')}")
            print(f"  最后更新: {data.get('last_update', '未知')}")
            print(f"  路由数量: {len(data.get('routes', []))}")
        else:
            print("  存储文件不存在")
    except Exception as e:
        print(f"  获取信息失败: {e}")


def main():
    """主函数"""
    print("RouteKeeper 使用示例")
    print("=" * 50)

    # 检查管理员权限
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("\n[错误] 此脚本需要管理员权限运行")
            print("请以管理员身份运行命令提示符或 PowerShell")
            sys.exit(1)
    except AttributeError:
        pass

    # 演示各项功能
    demo_list_routes()
    demo_add_route()
    demo_list_routes()
    demo_delete_route()
    demo_list_routes()
    demo_storage()


if __name__ == "__main__":
    main()
