"""JSON 持久化存储模块"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_storage_path() -> Path:
    """获取存储文件路径"""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("无法获取 LOCALAPPDATA 环境变量")
    return Path(local_app_data) / "RouteKeeper" / "routes.json"


def ensure_storage_dir() -> None:
    """确保存储目录存在"""
    path = get_storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)


def load_routes() -> dict[str, Any]:
    """加载路由数据"""
    path = get_storage_path()
    if not path.exists():
        return create_empty_db()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 验证基本结构
            if "version" not in data or "routes" not in data:
                return create_empty_db()
            return data
    except (json.JSONDecodeError, IOError):
        return create_empty_db()


def save_routes(data: dict[str, Any]) -> None:
    """保存路由数据"""
    ensure_storage_dir()
    path = get_storage_path()

    # 更新时间戳
    data["last_update"] = datetime.now(timezone.utc).isoformat()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_empty_db() -> dict[str, Any]:
    """创建空数据库"""
    return {
        "version": "1.0",
        "last_update": datetime.now(timezone.utc).isoformat(),
        "routes": [],
    }


def add_route_to_storage(
    destination: str,
    mask: str,
    gateway: str,
    metric: int,
    persistent: bool = False,
) -> None:
    """添加路由到存储"""
    data = load_routes()

    # 检查是否已存在
    for route in data["routes"]:
        if route["destination"] == destination and route["mask"] == mask:
            # 更新现有路由
            route["gateway"] = gateway
            route["metric"] = metric
            route["persistent"] = persistent
            route["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_routes(data)
            return

    # 添加新路由
    data["routes"].append({
        "destination": destination,
        "mask": mask,
        "gateway": gateway,
        "metric": metric,
        "persistent": persistent,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })

    save_routes(data)


def delete_route_from_storage(destination: str, mask: str) -> bool:
    """从存储中删除路由"""
    data = load_routes()
    original_count = len(data["routes"])

    data["routes"] = [
        r for r in data["routes"]
        if not (r["destination"] == destination and r["mask"] == mask)
    ]

    if len(data["routes"]) < original_count:
        save_routes(data)
        return True
    return False


def get_stored_routes() -> list[dict[str, Any]]:
    """获取存储的路由列表"""
    data = load_routes()
    return data["routes"]
