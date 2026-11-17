---
name: cad-verify
description: 在交付 Bambu Studio 切片前检查水密性、非流形边、法线、壁厚等可打印性，给出修复建议与格式规范（STL/3MF/gcode.3mf）。
whenToUse: 四层规格 LOCKED、准备切片或导出到 H2D 时使用。
---

# Skill: cad-verify（可打印性校验）

你在 L6 交付前做**打印性校验**。"能生成 3D ≠ 能打印"——必须过四道门槛。

## 本机前提

- Anaconda Python：`D:\Program Files\anaconda3\python.exe`，3.12.7（numpy 1.26.4 / scipy 1.13.1 / PIL / matplotlib 已装）。
- `trimesh` **已装**（5.2.1，用户已补齐）。可直接跑 `scripts/verify_stl.py`。
- 后台建模+校验闭环已实测：`scripts/build_from_params.py` → STL → `scripts/verify_stl.py` → `AUTO_PASS`。
- Blender 3D Print Toolbox 作为壁厚人工核验路径（Blender 5.3.0 自带插件需启用）。

## 重要：自动判定边界（实测踩坑，勿删）

- trimesh 读 STL 必须合并顶点（默认 `trimesh.load(path)` 或显式 `merge_vertices()`）；`process=False` 会因 STL 重复顶点把闭合体误判为 `is_watertight=False`。
- **壁厚不能用"最近顶点距离"当代理**——那测的是网格边长（垫片实测误报 0.21mm，实际壁厚 11.8mm）。三道自动门槛只管：水密 / 法线一致 / 体积为正；壁厚一律列为 `MANUAL_REQUIRED`，交 Blender 3D Print Toolbox → Check All → Thin Walls，**绝不伪造 PASS**。

## 四道门槛与判定阈值

| 门槛 | 检查项 | 通过标准 | 不通过后果 |
|---|---|---|---|
| 水密 | `mesh.is_watertight` | True | 切片报错/漏打印 |
| 非流形 | 非流形边数 | 0 | 壁厚异常、破面 |
| 法线 | 法线朝外 / 体积>0 | `mesh.volume > 0` | 切片内外颠倒 |
| 壁厚 | 最小壁厚 ≥ 喷嘴宽 | ≥ 0.4 mm（PLA/0.4 喷嘴） | 打印断裂/穿透 |

## trimesh 校验脚本

直接用工作区现成脚本（已实测，无需再写模板）：
```
python scripts/verify_stl.py <模型文件.stl> 0.4
```
它输出 JSON：三道自动门槛（watertight / winding_consistent / volume_positive）+ `verdict: AUTO_PASS|FAIL` + 壁厚 `MANUAL_REQUIRED`。

核心判定（供内联参考，勿用 process=False）：
```python
import trimesh
mesh = trimesh.load(r"<模型文件.stl>")   # 默认合并顶点；不要 process=False
if hasattr(mesh, "merge_vertices"): mesh.merge_vertices()
ok = mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
print("AUTO_PASS" if ok else "FAIL", "vol", round(mesh.volume,3), "bounds", mesh.extents)
```

手动补充（Blender 3D Print Toolbox）：启用插件 → 选对象 → `N` 面板 → 3D Print Toolbox → Check All（Non-Manifold / Intersections / Thin Walls），配合 `Make Solid` 自动修复。

## 修复建议流程

1. 水密 False / 非流形 > 0 → 回 `cad-blender-ops` 用布尔/合并/补面修复，或 Blender 3D Print Toolbox `Make Solid`。
2. 法线反向 → Blender `Recalculate Normals`（Shift+N）。
3. 壁厚不足 → 回 `cad-spec-driver` 调整 L3 参数（走确认门），不擅自加厚。
4. 修复后重跑校验，直到四道全过。

## 交付格式规范（Bambu Studio → H2D）

- 中间格式：STL（几何）或 3MF（几何+颜色+参数，Bambu Studio 原生）。
- 最终交付：Bambu Studio 切片后生成 `.gcode.3mf` / `.3mf` → 送 H2D。
- 切片参数（喷嘴/层高/材料）取 `params.json` 的 `material` 段，保持一致。

## 输出

给出一张校验表（四道门槛 ✓/✗ + 实测数值）+ 修复动作清单 + 最终交付文件路径。校验不过不得进入切片。
