# RouteKeeper - Windows 静态路由管理工具

一个用于管理 Windows 静态路由的工具，支持 CLI 和 GUI 两种界面，支持 IPv4 路由的查询、添加和删除，所有变更实时保存为 JSON 文件。

## 功能特性

- 查询系统所有 IPv4 静态路由
- 添加静态路由（支持 CIDR 格式）
- 删除静态路由（包含安全检查，防止删除默认路由）
- 所有变更实时保存为 JSON 文件
- 表格化展示路由信息
- 支持持久化路由标记
- **GUI 图形界面**：直观的图形化操作

## 系统要求

- Windows 10/11
- Python 3.10+
- 管理员权限（必须）

## 安装

### 方式一：直接运行 exe（推荐）

下载 `dist/RouteKeeper.exe`，右键以管理员身份运行。

### 方式二：Python 运行

```bash
# 克隆或下载项目
cd WinRouteTool

# 安装依赖
pip install -r requirements.txt

# 运行
python -m routekeeper list
```

### 方式三：安装为命令行工具

```bash
# 安装
pip install .

# 运行
routekeeper list
```

### 打包为 exe

```bash
# 安装 PyInstaller
pip install pyinstaller

# 执行打包
python build.py

# 输出文件：dist/RouteKeeper.exe
```

## 使用说明

### 查看所有路由

```bash
routekeeper list
```

输出示例：

```
              静态路由表
┌──────────────┬──────────────┬──────────────┬───────┬───────┐
│ 目的网络     │ 子网掩码     │ 网关         │ 跃点数 │ 持久化│
├──────────────┼──────────────┼──────────────┼───────┼───────┤
│ 0.0.0.0      │ 0.0.0.0      │ 192.168.1.1  │     1 │       │
│ 10.10.0.0    │ 255.255.0.0  │ 192.168.1.1  │    10 │   ✓   │
└──────────────┴──────────────┴──────────────┴───────┴───────┘

共 2 条路由
```

### 添加路由

```bash
# 基本格式
routekeeper add <CIDR> <网关>

# 示例：添加 10.10.0.0/16 路由，网关为 192.168.1.1
routekeeper add 10.10.0.0/16 192.168.1.1

# 指定跃点数
routekeeper add 10.10.0.0/16 192.168.1.1 --metric 10

# 标记为持久化（保存到 JSON）
routekeeper add 10.10.0.0/16 192.168.1.1 --persistent
```

### 删除路由

```bash
routekeeper delete <CIDR>

# 示例
routekeeper delete 10.10.0.0/16
```

### 查看存储信息

```bash
routekeeper info
```

### JSON 格式输出

```bash
routekeeper list --json
```

### 启动 GUI 图形界面

```bash
routekeeper gui
```

GUI 功能：
- 路由列表展示（表格形式）
- 添加路由（对话框输入）
- 删除选中路由（确认后删除，支持多选删除）
- 双击查看路由详情
- 实时刷新路由列表
- **多选支持**：按住 `Ctrl` 或 `Shift` 点击可多选路由
- **复制功能**：
  - 工具栏按钮：复制全部
  - 右键菜单：复制选中行、复制所有路由
  - 快捷键：`Ctrl+C` 复制选中行

## JSON 存储格式

路由数据保存在 `%LOCALAPPDATA%\RouteKeeper\routes.json`：

```json
{
  "version": "1.0",
  "last_update": "2026-05-14T18:00:00Z",
  "routes": [
    {
      "destination": "10.10.0.0",
      "mask": "255.255.0.0",
      "gateway": "192.168.1.1",
      "metric": 10,
      "persistent": true,
      "created_at": "2026-05-14T18:00:00Z",
      "updated_at": "2026-05-14T18:00:00Z"
    }
  ]
}
```

## 项目结构

```
WinRouteTool/
├── routekeeper/           # 主包
│   ├── __init__.py       # 包初始化
│   ├── __main__.py       # 入口点
│   ├── cli.py            # CLI 命令定义
│   ├── gui.py            # GUI 图形界面
│   ├── route_manager.py  # 路由管理核心逻辑
│   ├── win_api.py        # Windows API 调用
│   └── storage.py        # JSON 持久化
├── pyproject.toml        # 项目配置
├── requirements.txt      # 依赖列表
└── README.md            # 使用文档
```

## 安全说明

- 此工具需要管理员权限才能修改系统路由表
- 内置安全检查，防止删除默认路由（0.0.0.0/0）
- 所有变更都会记录到 JSON 文件，便于审计

## 注意事项

- 仅支持 IPv4 路由
- 必须以管理员身份运行命令提示符或 PowerShell
- 删除路由时会同时从系统和 JSON 文件中移除

## 许可证

MIT License
