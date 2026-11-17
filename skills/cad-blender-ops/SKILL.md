---
name: cad-blender-ops
description: 通过 Blender（MCP 实时交互或后台 bpy 脚本）在本机 Blender 5.3.0 创建/修改/查询几何、执行 Python、取预览、导出 STL 的模板库；含已核实环境与避坑要点。
whenToUse: 确认门"生成候选几何"步骤、需要在 Blender 里真正建出几何并回传证据时使用。
---

# Skill: cad-blender-ops（Blender 几何操作模板库）

你是 L1/L2 桥接的执行手，负责把"候选几何"在 Blender 里真正做出来，并把证据回传。**L2 有两条通道：MCP（实时交互）与 bpy 后台 runner（无需 GUI，已实测跑通）。优先用 MCP；若 Blender 端 server 未启动，退回后台 runner。**

## 本机已核实环境

- Blender：`D:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe`，版本 **5.3.0**（2026-11-17 实测，已从 5.2.2 升级）。
- MCP 插件：已装到 `C:\Users\Tim\AppData\Roaming\Blender Foundation\Blender\5.3\scripts\addons\blender_mcp.py`。
- DSH MCP bridge：bundle `@local/blender-mcp-bridge` 已启用，`mcp__blender__*` 工具（execute_blender_code / look / get_scene_info / get_addon_status 等）已注册。需在 Blender GUI 启用插件并 Start MCP Server 后连通。
- 后台可执行 Python：`blender.exe --background --python <脚本>` 或 `--python-expr "<表达式>"`。
- 无界面服务器场景适合：用后台模式跑脚本 → 导出 STL / 存 .blend / 截预览。

## 选择通道

- **MCP 通道**（需 GUI）：先 `mcp__blender__get_addon_status` 探测连通；连通后用 `mcp__blender__execute_blender_code` 跑下面模板，`mcp__blender__look` 取预览。
- **后台 runner**（无需 GUI，推荐批量/无人值守）：`scripts/build_from_params.py -- <params.json> <out_dir>` 已封装基本体+布尔+证据+导出，见工作区 README。

## 状态与命名约定（与 spec 对齐）

- 一个候选 = 一个 `.blend` 工程文件，命名 `<spec_id>_<层>_候选<X>.blend`，存 `_cad_workflow/projects/`。
- 保存检查点时复制 `.blend` 为 `v<N>_<层名>.blend`。
- Blender 对象名用 `P01_特征` 形式（对应 spec 的部件 ID / 特征 ID）。
- 因 Blender **无原生参数化特征树**：把关键参数存为对象的自定义属性（`obj["param_key"] = value`），并同步到 `params.json`，作为"参数化"的替代。

## 核心操作模板（用 bpy，MCP 接入后由 MCP 转发或后台脚本执行）

**建基本体 + 布尔（做孔/槽）：**
```python
import bpy
bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 10))  # 边长20，底面贴地
base = bpy.context.object
base.name = "P01_base"
bpy.ops.mesh.primitive_cylinder_add(radius=3, depth=25, location=(0, 0, 10))
cutter = bpy.context.object
bpy.context.view_layer.objects.active = base
mod = base.modifiers.new("hole", 'BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
bpy.ops.object.modifier_apply(modifier="hole")
bpy.data.objects.remove(cutter, do_unlink=True)
```

**存关键参数为自定义属性：**
```python
base["hole_d"] = 6.0
base["envelope_l"] = 20.0
```

**导出 STL（Bambu Studio 可导入）：**
```python
bpy.ops.wm.stl_export(filepath=r"<工作区>\_cad_workflow\output\candidate.stl",
                      export_selected_objects=True, apply_modifiers=True)
```

**取预览截图**：优先用 MCP 视口截图工具；无 MCP 时用 Blender 渲染一张小图（`bpy.ops.render.render(write_still=True)`）作为预览，路径回传给确认门。

**取几何证据（面数/尺寸/水密）**：
```python
# 面数、包围盒尺寸
me = base.data
dims = tuple(round(v, 3) for v in base.dimensions)
faces = len(me.polygons)
print("DIMS", dims, "FACES", faces)
# 水密：用 bmesh 检查非流形边
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
nonmanifold = [e for e in bm.edges if not e.is_manifold]
print("NONMANIFOLD_EDGES", len(nonmanifold))
bm.free()
```
（更严格的水密/壁厚校验交 `cad-verify` 用 trimesh 做。）

## 避坑

- Blender 5.x 的 STL 导出算子是 `bpy.ops.wm.stl_export`（旧版 `export_mesh.stl` 已弃用）。
- 布尔后要 `modifier_apply`，否则导出可能不带孔。
- 单位用 mm 思维：Blender 默认单位 m，建模时按数值即 mm 处理，导出 STL 不带单位（切片软件按 mm 解释），保持一致即可。
- 后台模式没有 GUI，视口截图只能用渲染替代；确认门要说明证据类型。
- **MCP 未接入前的临时替代**：用 `--background --python 脚本` 跑上面模板，同样能产出几何+证据，只是没有实时交互。

## 交付

几何 + 证据（截图/尺寸/面数/非流形边数）回传给 `cad-confirm-gate`；不自行写入 spec，不替用户确认。
