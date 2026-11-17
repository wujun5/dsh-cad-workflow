# FreeCAD MCP 桥接（bundled）

把 DSH 连接到本机 FreeCAD，用于**功能件 / 装配 / 公差件**的参数化建模（与 Blender 造型件分流）。

## 组件
- **Addon（FreeCAD 内）**：`MCP Addon` workbench → `Start RPC Server`，默认监听 `127.0.0.1:9875`。
  - 已安装到 `C:\Users\Tim\AppData\Roaming\FreeCAD\v27-1\Mod\FreeCADMCP`（v0.1.32）。
- **MCP Server（DSH 启动）**：`uvx freecad-mcp --host localhost --freecadcmd <path>`，stdio 传输。

## 本机事实（2026-11-17 实测）
- FreeCAD **27.1.0 Weekly**（winget `FreeCAD.FreeCAD.Weekly`），GUI：`D:\Program Files\FreeCAD 27.1\bin\FreeCAD.exe`。
- Headless：`D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe`（已验证可建模并导出 STL）。
- 用户 AppData：`C:\Users\Tim\AppData\Roaming\FreeCAD\v27-1\`（addon Mod 目录在此）。

## 启用步骤（一次性）
1. 启动 FreeCAD GUI（若已开需重启以加载新 addon）。
2. 工作台下拉选 **MCP Addon**。
3. 工具栏点 **Start RPC Server**，确认状态栏出现监听地址 `127.0.0.1:9875` 与 PID。
4. 在 DSH 侧调用 `get_rpc_status` / `mcp__freecad__*` 验证。

## 注意
- addon 与 `freecad-mcp` 包独立更新；首次连接会比对协议版本，版本不符会告警。二者当前均为 0.1.32。
- 端口 9875 是 addon 的 XML-RPC，不是 MCP 的 HTTP/SSE 端点；MCP 本身走 stdio。
- Windows 若报 `EFTYPE`/`uv_spawn`，可改用 `cmd /c freecad-mcp`（本 bundle 暂用直接 uvx）。

## 替代路线（更优，无需 GUI）
对精确功能件，还可用 `FreeCADCmd.exe` headless 跑 Python 脚本（"代码即模型"），无 RPC、无需 GUI、可批量/可复现。见工作区 `_cad_workflow/scripts/build_freecad_from_params.py`。这条路线与 MCP 互补，按场景选择。
