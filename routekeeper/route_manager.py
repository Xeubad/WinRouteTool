"""路由管理核心逻辑"""

from dataclasses import dataclass
from typing import Optional

try:
    from routekeeper import win_api, storage
except ImportError:
    from . import win_api, storage


@dataclass
class Route:
    """路由条目"""
    destination: str
    mask: str
    gateway: str
    metric: int
    interface_index: int = 0
    is_persistent: bool = False


def parse_cidr(cidr: str) -> tuple[str, str]:
    """解析 CIDR 格式（如 10.10.0.0/16）"""
    if "/" not in cidr:
        raise ValueError(f"无效的 CIDR 格式: {cidr}，应为 网络/掩码长度")

    parts = cidr.split("/")
    if len(parts) != 2:
        raise ValueError(f"无效的 CIDR 格式: {cidr}")

    network = parts[0]
    try:
        prefix_len = int(parts[1])
    except ValueError:
        raise ValueError(f"无效的掩码长度: {parts[1]}")

    if prefix_len < 0 or prefix_len > 32:
        raise ValueError(f"掩码长度必须在 0-32 之间: {prefix_len}")

    mask = win_api.cidr_to_mask(prefix_len)
    return network, mask


def to_cidr(destination: str, mask: str) -> str:
    """将网络地址和掩码转换为 CIDR 格式"""
    prefix_len = win_api.mask_to_cidr(mask)
    return f"{destination}/{prefix_len}"


def list_routes() -> list[Route]:
    """列出所有路由"""
    # 从 Windows API 获取路由表
    system_routes = win_api.get_routes()

    # 从存储获取持久化标记
    stored_routes = storage.get_stored_routes()
    stored_map = {}
    for r in stored_routes:
        key = (r["destination"], r["mask"])
        stored_map[key] = r

    routes = []
    for sr in system_routes:
        key = (sr.destination, sr.mask)
        is_persistent = False
        if key in stored_map:
            is_persistent = stored_map[key].get("persistent", False)

        route = Route(
            destination=sr.destination,
            mask=sr.mask,
            gateway=sr.gateway,
            metric=sr.metric,
            interface_index=sr.interface_index,
            is_persistent=is_persistent,
        )
        routes.append(route)

    return routes


def add_route(
    cidr: str,
    gateway: str,
    metric: int = 0,
    persistent: bool = False,
) -> Route:
    """添加路由

    Args:
        metric: 路由跃点数。0 表示由 Windows 自动分配（默认行为）。
    """
    destination, mask = parse_cidr(cidr)

    # 验证网关地址格式
    try:
        win_api.ip_to_dword(gateway)
    except ValueError:
        raise ValueError(f"无效的网关地址: {gateway}")

    # 调用 Windows API 添加路由
    win_api.add_route(
        destination=destination,
        mask=mask,
        gateway=gateway,
        metric=metric,
    )

    # 保存到存储
    storage.add_route_to_storage(
        destination=destination,
        mask=mask,
        gateway=gateway,
        metric=metric,
        persistent=persistent,
    )

    return Route(
        destination=destination,
        mask=mask,
        gateway=gateway,
        metric=metric,
        is_persistent=persistent,
    )


def delete_route(cidr: str) -> None:
    """删除路由"""
    destination, mask = parse_cidr(cidr)

    # 安全检查：防止删除默认路由
    if destination == "0.0.0.0" and mask == "0.0.0.0":
        raise ValueError("安全限制：不允许删除默认路由 (0.0.0.0/0)")

    # 查找路由以获取网关信息
    route = win_api.find_route(destination, mask)
    if not route:
        raise ValueError(f"路由不存在: {cidr}")

    # 调用 Windows API 删除路由
    win_api.delete_route(
        destination=destination,
        mask=mask,
        gateway=win_api.dword_to_ip(route.dwForwardNextHop),
        interface_index=route.dwForwardIfIndex,
    )

    # 从存储中删除
    storage.delete_route_from_storage(destination, mask)


def get_route(cidr: str) -> Optional[Route]:
    """获取指定路由"""
    destination, mask = parse_cidr(cidr)

    routes = list_routes()
    for route in routes:
        if route.destination == destination and route.mask == mask:
            return route

    return None
