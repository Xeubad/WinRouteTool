"""Windows API 调用模块，用于管理路由表"""

import ctypes
import subprocess
from ctypes import wintypes
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

# Windows API 常量
ERROR_SUCCESS = 0
ERROR_NO_DATA = 232
ERROR_BUFFER_OVERFLOW = 111
ERROR_INSUFFICIENT_BUFFER = 122


class ForwardType(IntEnum):
    """路由类型"""
    OTHER = 1
    INVALID = 2
    DIRECT = 3
    INDIRECT = 4


class ForwardProto(IntEnum):
    """路由协议"""
    OTHER = 1
    LOCAL = 2
    NETMGMT = 3
    ICMP = 4
    EGP = 5
    GGP = 6
    HELLO = 7
    RIP = 8
    IS_IS = 9
    ES_IS = 10
    CISCO = 11
    BBN = 12
    OSPF = 13
    BGP = 14


@dataclass
class RouteEntry:
    """路由表条目"""
    destination: str
    mask: str
    gateway: str
    interface_index: int
    metric: int
    route_type: ForwardType
    protocol: ForwardProto
    age: int
    next_hop_as: int = 0


class MIB_IPFORWARDROW(ctypes.Structure):
    """IPv4 路由表行结构"""
    _fields_ = [
        ("dwForwardDest", wintypes.DWORD),
        ("dwForwardMask", wintypes.DWORD),
        ("dwForwardPolicy", wintypes.DWORD),
        ("dwForwardNextHop", wintypes.DWORD),
        ("dwForwardIfIndex", wintypes.DWORD),
        ("dwForwardType", wintypes.DWORD),
        ("dwForwardProto", wintypes.DWORD),
        ("dwForwardAge", wintypes.DWORD),
        ("dwForwardNextHopAS", wintypes.DWORD),
        ("dwForwardMetric1", wintypes.DWORD),
        ("dwForwardMetric2", wintypes.DWORD),
        ("dwForwardMetric3", wintypes.DWORD),
        ("dwForwardMetric4", wintypes.DWORD),
        ("dwForwardMetric5", wintypes.DWORD),
    ]


class MIB_IPFORWARDTABLE(ctypes.Structure):
    """IPv4 路由表结构"""
    _fields_ = [
        ("dwNumEntries", wintypes.DWORD),
        ("table", MIB_IPFORWARDROW * 1),
    ]


# 加载 Windows API
iphlpapi = ctypes.WinDLL("iphlpapi", use_last_error=True)

# GetIpForwardTable
GetIpForwardTable = iphlpapi.GetIpForwardTable
GetIpForwardTable.argtypes = [
    ctypes.POINTER(MIB_IPFORWARDTABLE),
    ctypes.POINTER(wintypes.ULONG),
    wintypes.BOOL,
]
GetIpForwardTable.restype = wintypes.DWORD


import socket
import struct


def ip_to_dword(ip: str) -> int:
    """将 IP 地址字符串转换为 DWORD（小端字节序）"""
    return struct.unpack("<I", socket.inet_aton(ip))[0]


def dword_to_ip(dword: int) -> str:
    """将 DWORD（小端字节序）转换为 IP 地址字符串"""
    return socket.inet_ntoa(struct.pack("<I", dword))


def cidr_to_mask(cidr: int) -> str:
    """将 CIDR 前缀长度转换为子网掩码"""
    if cidr < 0 or cidr > 32:
        raise ValueError(f"无效的 CIDR 前缀长度: {cidr}")
    mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
    return socket.inet_ntoa(struct.pack(">I", mask))


def mask_to_cidr(mask: str) -> int:
    """将子网掩码转换为 CIDR 前缀长度"""
    dword = ip_to_dword(mask)
    # ip_to_dword 返回小端序，需转回大端序再数前导 1
    big = struct.unpack(">I", struct.pack("<I", dword))[0]
    cidr = 0
    while big & 0x80000000:
        cidr += 1
        big <<= 1
    return cidr


def get_routes() -> list[RouteEntry]:
    """获取所有 IPv4 路由"""
    # 第一次调用获取所需缓冲区大小
    size = wintypes.ULONG(0)
    result = GetIpForwardTable(None, ctypes.byref(size), False)

    if result != ERROR_BUFFER_OVERFLOW and result != ERROR_INSUFFICIENT_BUFFER:
        raise ctypes.WinError(result)

    # 分配缓冲区
    buf = ctypes.create_string_buffer(size.value)

    # 第二次调用获取路由表
    result = GetIpForwardTable(ctypes.cast(buf, ctypes.POINTER(MIB_IPFORWARDTABLE)), ctypes.byref(size), False)
    if result != ERROR_SUCCESS:
        raise ctypes.WinError(result)

    # 获取条目数
    num_entries = ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD)).contents.value

    # 计算每条记录的偏移量
    row_size = ctypes.sizeof(MIB_IPFORWARDROW)
    header_size = ctypes.sizeof(wintypes.DWORD)  # dwNumEntries 的大小

    routes = []
    for i in range(num_entries):
        # 计算当前行的偏移量
        offset = header_size + i * row_size
        row_ptr = ctypes.cast(ctypes.byref(buf, offset), ctypes.POINTER(MIB_IPFORWARDROW))
        row = row_ptr.contents

        route = RouteEntry(
            destination=dword_to_ip(row.dwForwardDest),
            mask=dword_to_ip(row.dwForwardMask),
            gateway=dword_to_ip(row.dwForwardNextHop),
            interface_index=row.dwForwardIfIndex,
            metric=row.dwForwardMetric1,
            route_type=ForwardType(row.dwForwardType),
            protocol=ForwardProto(row.dwForwardProto),
            age=row.dwForwardAge,
            next_hop_as=row.dwForwardNextHopAS,
        )
        routes.append(route)

    return routes


def _find_interface_for_gateway(gateway: str) -> int:
    """根据网关 IP 自动查找合适的接口索引"""
    gateway_dword = ip_to_dword(gateway)

    routes = get_routes()
    # 1. 精确匹配：已存在到该网关的路由，复用其接口
    for r in routes:
        if ip_to_dword(r.gateway) == gateway_dword and r.interface_index != 0:
            return r.interface_index

    # 2. 子网匹配：网关落在某接口直连子网内
    for r in routes:
        if r.route_type == ForwardType.DIRECT and r.interface_index != 0:
            net = ip_to_dword(r.destination)
            msk = ip_to_dword(r.mask)
            if (gateway_dword & msk) == (net & msk):
                return r.interface_index

    return 0


CREATE_NO_WINDOW = 0x08000000


def _run_route(cmd: list[str]) -> subprocess.CompletedProcess:
    """执行 route 命令，兼容无控制台的 GUI 环境"""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )


def add_route(
    destination: str,
    mask: str,
    gateway: str,
    interface_index: int = 0,
    metric: int = 0,
) -> None:
    """添加静态路由（通过 route 命令）

    Args:
        metric: 路由跃点数。0 表示由 Windows 自动分配。
    """
    cmd = ["route", "add", destination, "mask", mask, gateway]
    if metric > 0:
        cmd.extend(["metric", str(metric)])

    result = _run_route(cmd)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        raise OSError(f"添加路由失败: {err}")


def delete_route(
    destination: str,
    mask: str,
    gateway: str,
    interface_index: int = 0,
) -> None:
    """删除静态路由（通过 route 命令）"""
    cmd = ["route", "delete", destination, "mask", mask, gateway]

    result = _run_route(cmd)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        raise OSError(f"删除路由失败: {err}")


def find_route(destination: str, mask: str) -> Optional[MIB_IPFORWARDROW]:
    """查找路由"""
    routes = get_routes()
    dest_dword = ip_to_dword(destination)
    mask_dword = ip_to_dword(mask)

    for route in routes:
        if (ip_to_dword(route.destination) == dest_dword and
                ip_to_dword(route.mask) == mask_dword):
            row = MIB_IPFORWARDROW()
            row.dwForwardDest = dest_dword
            row.dwForwardMask = mask_dword
            row.dwForwardNextHop = ip_to_dword(route.gateway)
            row.dwForwardIfIndex = route.interface_index
            row.dwForwardType = route.route_type
            row.dwForwardProto = route.protocol
            row.dwForwardAge = route.age
            row.dwForwardNextHopAS = route.next_hop_as
            row.dwForwardMetric1 = route.metric
            return row

    return None
