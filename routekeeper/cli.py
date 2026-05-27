"""CLI 命令定义"""

import ctypes
import sys

import click
from rich.console import Console
from rich.table import Table

try:
    from routekeeper import __version__, route_manager, storage
except ImportError:
    from . import __version__, route_manager, storage

console = Console()


def check_admin() -> None:
    """检查管理员权限"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            console.print("[red]错误: 此程序需要管理员权限运行[/red]")
            console.print("[yellow]请以管理员身份运行命令提示符或 PowerShell[/yellow]")
            sys.exit(1)
    except AttributeError:
        # 非 Windows 系统
        pass


@click.group()
@click.version_option(version=__version__, prog_name="RouteKeeper")
def cli() -> None:
    """RouteKeeper - Windows 静态路由管理工具"""
    pass


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="输出 JSON 格式")
def list(output_json: bool) -> None:
    """列出所有静态路由"""
    check_admin()
    try:
        routes = route_manager.list_routes()

        if not routes:
            console.print("[yellow]没有找到路由[/yellow]")
            return

        if output_json:
            import json
            data = {
                "version": "1.0",
                "route_count": len(routes),
                "routes": [
                    {
                        "destination": r.destination,
                        "mask": r.mask,
                        "gateway": r.gateway,
                        "metric": r.metric,
                        "persistent": r.is_persistent,
                        "cidr": route_manager.to_cidr(r.destination, r.mask),
                    }
                    for r in routes
                ],
            }
            console.print_json(json.dumps(data, indent=2))
        else:
            table = Table(title="静态路由表", show_lines=True)
            table.add_column("目的网络", style="cyan")
            table.add_column("子网掩码", style="cyan")
            table.add_column("网关", style="green")
            table.add_column("跃点数", justify="right")
            table.add_column("持久化", justify="center")

            for route in sorted(routes, key=lambda r: r.destination):
                table.add_row(
                    route.destination,
                    route.mask,
                    route.gateway,
                    str(route.metric),
                    "✓" if route.is_persistent else "",
                )

            console.print(table)
            console.print(f"\n共 {len(routes)} 条路由")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("cidr")
@click.argument("gateway")
@click.option("--metric", "-m", default=0, help="路由跃点数 (0=Windows 自动分配，以太网通常 25~55)")
@click.option("--persistent", "-p", is_flag=True, help="持久化保存")
def add(cidr: str, gateway: str, metric: int, persistent: bool) -> None:
    """添加静态路由

    CIDR 格式: 网络地址/掩码长度 (如 10.10.0.0/16)
    GATEWAY: 网关地址 (如 192.168.1.1)
    """
    check_admin()
    try:
        route = route_manager.add_route(
            cidr=cidr,
            gateway=gateway,
            metric=metric,
            persistent=persistent,
        )

        console.print(f"[green]成功添加路由:[/green]")
        console.print(f"  目的网络: {route.destination}/{route_manager.win_api.mask_to_cidr(route.mask)}")
        console.print(f"  网关: {route.gateway}")
        console.print(f"  跃点数: {route.metric}")
        if persistent:
            console.print(f"  [yellow]已标记为持久化[/yellow]")

    except ValueError as e:
        console.print(f"[red]参数错误: {e}[/red]")
        sys.exit(1)
    except OSError as e:
        console.print(f"[red]系统错误: {e}[/red]")
        console.print("[yellow]请确认管理员权限和网络配置[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("cidr")
def delete(cidr: str) -> None:
    """删除静态路由

    CIDR 格式: 网络地址/掩码长度 (如 10.10.0.0/16)
    """
    check_admin()
    try:
        route_manager.delete_route(cidr)
        console.print(f"[green]成功删除路由: {cidr}[/green]")

    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)
    except OSError as e:
        console.print(f"[red]系统错误: {e}[/red]")
        console.print("[yellow]请确认管理员权限和路由存在[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        sys.exit(1)


@cli.command()
def info() -> None:
    """显示存储信息"""
    try:
        path = storage.get_storage_path()
        console.print(f"存储路径: {path}")

        if path.exists():
            data = storage.load_routes()
            console.print(f"版本: {data.get('version', '未知')}")
            console.print(f"最后更新: {data.get('last_update', '未知')}")
            console.print(f"路由数量: {len(data.get('routes', []))}")
        else:
            console.print("[yellow]存储文件不存在[/yellow]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)


@cli.command()
def gui() -> None:
    """启动图形界面"""
    try:
        try:
            from routekeeper.gui import main as gui_main
        except ImportError:
            from .gui import main as gui_main
        gui_main()
    except ImportError as e:
        console.print(f"[red]错误: 无法加载 GUI 模块: {e}[/red]")
        console.print("[yellow]请确认 tkinter 已安装[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)


def main() -> None:
    """主入口"""
    cli()


if __name__ == "__main__":
    main()
