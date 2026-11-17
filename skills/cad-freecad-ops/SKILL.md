---
name: cad-freecad-ops
description: 通过 FreeCAD 在本机创建/修改/查询精确功能件几何（B-rep 实体），支持 MCP 实时通道、MCP headless、FreeCADCmd 代码即模型 runner 三种方式；导出 STL/STEP 并回传几何证据。用于功能件/装配/公差件，是 Blender 造型件的互补引擎。
whenToUse: 确认门"生成候选几何"步骤，且模型判为功能件（精确尺寸/孔位/公差/装配）而非造型件时；需要 OCCT B-rep 精确几何或 STEP 导出时用。
---

# Skill: cad-freecad-ops（FreeCAD 几何操作模板库）

你是 L1/L2 桥接的执行手，负责把"候选几何"在 FreeCAD 里真正做出来并回传证据。**FreeCAD 有三条通道，按场景选择；对精确功能件，headless 代码路线通常优于 MCP 实时通道。**

## 三条通道（按优先级）

| 通道 | 命令 | 需 GUI | 适用 |
|---|---|---|---|
| **A. 代码即模型 headless**（推荐） | `FreeCADCmd.exe build_freecad_from_params.py`（env 传参） | 否 | 精确功能件、批量、可复现、CI；B-rep 精确几何 + STEP |
| **B. MCP headless** | `mcp__freecad__execute_code_headless` | 否 | 快速脚本、无本地 shell 时；底层同 A |
| **C. MCP 实时** | `mcp__freecad__execute_code` | 是（需 Start RPC Server） | 需操作 GUI 文档、取视口、FEM、装配交互 |

**关键事实（实测）**：通道 B 在 GUI RPC server 未启动时仍可用（走 `--freecadcmd` 独立进程），比 Blender MCP 灵活；通道 C 需用户在 GUI 点 Start RPC Server（127.0.0.1:9875）。

## 本机已核实环境（2026-11-17）

- FreeCAD **27.1.0 Weekly**（winget `FreeCAD.FreeCAD.Weekly`）。
  - GUI：`D:\Program Files\FreeCAD 27.1\bin\FreeCAD.exe`
  - Headless：`D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe`（已验证 `FC_VERSION ['27','1','0',...]`）
- Addon：MCP Addon v0.1.32 已装到 `C:\Users\Tim\AppData\Roaming\FreeCAD\v27-1\Mod\FreeCADMCP`（权威 AppData 由 `FreeCAD.getUserAppDataDir()` 确认）。
- DSH bundle：`@local/freecad-mcp-bridge` 已启用，`mcp__freecad__*` **18 个工具**已注册（create_document/create_object/edit_object/execute_code/execute_code_headless/get_rpc_status/get_view/run_fem_analysis 等）。
- addon 与 uvx 包协议版本一致（均 0.1.32）。

## 通道 A：代码即模型 runner（首选）

脚本：`_cad_workflow/scripts/build_freecad_from_params.py`（与 blender runner 同 params schema）。

```
$env:CAD_PARAMS = "<params.json 绝对路径>"
$env:CAD_OUT    = "<out_dir 绝对路径>"
& "D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe" "<...>\build_freecad_from_params.py"
```

**已实测**（washer-test，D30/孔6.4/厚3）：
- B-rep 证据：dims=[30,30,3]mm、`is_valid=true`、`is_closed=true`、solids=1、faces=**4**（精确解析面）、体积 2024.065mm³
- 产物：`washer-test-freecad.stl` + `.step`（112 实体）+ `.build-evidence.json`
- trimesh 校验 STL：`AUTO_PASS`（watertight/winding/volume 全过）

## 通道 B：MCP headless

```
mcp__freecad__execute_code_headless({ code: "import FreeCAD, Part; ..." })
```
实测返回 `MCP_HEADLESS_OK True 1000.0`，GUI 未启动也可用。适合临时小脚本、不便开本地 shell 时。

## 通道 C：MCP 实时（需用户手动一次性启动）

1. 启动 FreeCAD GUI（新装 addon 需重启加载）。
2. 工作台下拉选 **MCP Addon** → 工具栏点 **Start RPC Server**（默认 `127.0.0.1:9875`）。
3. DSH 侧 `mcp__freecad__get_rpc_status` 验证连通（未启动时该工具会报错，属预期）。
4. 连通后用 `mcp__freecad__create_object`（Part::Box/Cylinder 等）、`edit_object`（填 Length/Width/Height/Radius）、`get_objects`/`get_view`、`run_fem_analysis`。

## 核心操作模板（Part B-rep）

```python
import FreeCAD as App, Part
d = App.newDocument("P01")
box = d.addObject("Part::Box", "Box")
box.Length = 30; box.Width = 20; box.Height = 3
d.recompute()
shape = box.Shape
print("valid", shape.isValid(), "closed", shape.isClosed(), "vol", round(shape.Volume,3))
shape.exportStl(r"<out>\part.stl")
shape.exportStep(r"<out>\part.step")   # FreeCAD 独有优势：精确参数化交换
```
布尔做孔：`base.cut(cutter).removeSplitter()`；倒角/圆角：`shape.makeFillet(r, edges)`。

## 状态与交付

- 一个候选 = 一个 `.FCStd` 工程（通道 C 可存）；通道 A 用 params.json + B-rep 证据 json 作为事实源。
- 命名 `<spec_id>_<层>_候选<X>`；检查点 `v<N>_<层名>.FCStd` 或 `v<N>.params.json`。
- 几何 + 证据（dims/valid/closed/solids/faces/volume + 预览）回传 `cad-confirm-gate`；不自行写 spec。

## 避坑（本轮真实踩坑）

1. **FreeCADCmd 把每个 CLI 参数当文件打开**：params.json 作为 arg 会被 GBK 解码报 `UnicodeDecodeError`（中文注释）→ 改用**环境变量** `CAD_PARAMS`/`CAD_OUT` 传参，只留脚本一个文件参数；读文件用 `encoding="utf-8-sig"`。
2. **FreeCADCmd 用 exec 加载脚本，`__name__ != "__main__"`**：`if __name__ == "__main__": main()` 不触发 → runner 底部直接 `main()`。
3. 无论 MCP 还是 headless，导出的 STL 都要交 `cad-verify`（trimesh）复核水密/法线。
4. 端口 9875 是 addon XML-RPC，不是 MCP 的 HTTP/SSE 端点；MCP 走 stdio。
5. Windows 若报 `EFTYPE`/`uv_spawn`，换 `cmd /c freecad-mcp`（本 bundle 暂用直接 uvx，本机实测可启动）。
