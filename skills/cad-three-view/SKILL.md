---
name: cad-three-view
description: 把机械制图的三视图（主/俯/左，带尺寸标注的工程图、DWG/DXF 矢量图或 SVG）重建为可打印 3D 模型的编排 skill。读图→尺寸映射→params→FreeCAD headless 建模→校验。三视图重建是病态问题，本 skill 采用"参数化精确重建"路线，适合带尺寸标注、可判定为回转体/基本体组合的零件；含真实 DWG 逆向（AutoCAD accoreconsole 转 DXF + ezdxf 解析实体坐标反推尺寸）的实测流程。
whenToUse: 用户给出三视图工程图（DWG/DXF/PDF/图片/SVG，带尺寸标注或从 CAD 导出）并要求生成 3D/可打印模型，或要求把 CAD 三视图"逆向"为 3D 时；或用户问"能否从三视图/CAD 2D 图生成三维模型"时。由 cad-spec-driver 在 L0 判定输入形式为三视图时调用。
---

# Skill: cad-three-view（三视图→3D 重建编排器）

把三视图这类 **L5 输入形式** 收敛为 L3 `params.json`，再交给既有引擎链路建模。换输入方式不动 L1/L2——这是六层栈的设计收益。

## 核心事实（先向用户讲清，避免误解）

1. **TechDraw 是反方向**：3D → 工程图。没有"一键三视图→3D"按钮。
2. **重建是病态问题（ill-posed）**：同一三视图可对应多个形体（主视图都是矩形的圆柱与方柱）。纯自动重建是二十年未完全解决的学术难题（ENSAM 两阶段线框法、CAD Journal 变分几何+复合图法、ICCV2023 PlankAssembly 学习式 shape program）——证据质量偏低，方向可信但无成熟通用开源工具链。
3. **出路**：带尺寸标注的工程图 + 判定为回转体/基本体组合 → 可唯一确定 → 走参数化精确重建。

## 三条路线（按输入与精度选）

| 路线 | 做法 | 适用 | 局限 |
|---|---|---|---|
| **A. 参数化精确重建**（首选） | 读尺寸标注→`params.json`→FreeCAD headless（复用 `build_freecad_from_params.py`） | 带尺寸标注、回转体/基本体组合 | 需人有/视觉模型能读图；斜面/相贯线需人工补 L2 |
| **B. 视觉外壳 visual hull** | 三向轮廓反投影求交 | 只有剪影/照片、无尺寸；L0 大方向预览 | 只能得最大外包络，丢孔/凹坑/台阶（真实形体超集） |
| **C. 线稿自动识别** | 提线→线框对应→B-rep | 研究 | 复杂件易失败，无成熟工具 |

用户素材是"带尺寸标注的工程图"→ 走 A。

## 真实 DWG/DXF 逆向流程（本机实测，2026-11-18）

用户给的是 CAD 原生 `.dwg`（如 `part.dwg`，AC1032=AutoCAD 2018）时：

1. **探测版本**：读 DWG 前 6 字节（`AC1032`=2018 / `AC1027`=2013 / `AC1015`=2000 / `AC1009`=R12）。
2. **转 DXF**：ezdxf 不能直接读 DWG。本机有 **AutoCAD 2026**，用无 GUI 核心控制台：
   - `accoreconsole.exe` 位于 `D:\Program Files\AutoCAD\AutoCAD 2026\`
   - 转换脚本 `dwg2dxf.scr`：`FILEDIA/0` → `_.DXFOUT <out.dxf> 16`（16=2018 格式）→ `_.QUIT/_Y`
   - 命令：`accoreconsole.exe /i <in.dwg> /s <dwg2dxf.scr>`
   - 无 AutoCAD 时替代：ODA File Converter（ezdxf addon odafc）或 LibreCAD/QCAD。
3. **解析实体**：ezdxf `ezdxf.readfile(dxf)`，遍历 modelspace。按图层区分语义（Outlines 实线 / Hidden 虚线 / Centerlines 中心线 / Dimensions 标注）。
4. **反推尺寸**：标注层常为空，尺寸要从实体坐标反推——LINE 端点、CIRCLE 半径/圆心、ARC 半径/角度；先识别三视图在模型空间的排布区域（自由排布，未必标准三角配置），再按"长对正/高平齐/宽相等"映射到参数。
5. **单位**：读 `$INSUNITS`（6=mm）/ `$MEASUREMENT`（1=公制）。
6. **校验**：用视图间约束交叉验证（总高=底+立、槽底位置两视图一致、孔位主/俯一致），并做**模型三向投影自检**（把生成 STL 的顶点投影到 3 平面，范围应等于各视图的 DXF 包围盒）。

> 实测案例：`part.dwg` U 型槽支座 → 底座30×14×8 + 前立板30×8×14 + R10 半圆槽 + 2×Ø8 通孔；生成模型 dims=[30,14,22]、14 B-rep 面、三向投影全部吻合、STL AUTO_PASS。

## 工作流（对齐确认门协议）

1. **L0 判定**：确认是三视图、判定形体类别（回转体 / 基本体叠加 / 含斜面相贯线）。
   - 判回转体：主/左视图轮廓相同且俯视图为同心圆 → 可由少数参数唯一确定。
   - 有无法由三视图判定的特征（斜孔/非对称切除/相贯）→ 在 L2 请求用户补充说明，不臆断。
2. **读图（读图→参数映射）**：按"长对正、高平齐、宽相等"逐尺寸读，写入 `*-spec.md` 的对照表（观测像素/标注 ÷ 比例 → 参数值）。**当前模型不支持图像输入**：优先用 SVG/DXF 等矢量图（文本可读、可审计）；若是位图，请用户口述尺寸或提供矢量源。
3. **一致性校验**：用视图间约束交叉验证（如主视图总高 = 底座高 + 凸台高）。
4. **L3 写 params**：`shape` + `params` 写入 `*-params.json`（见 `examples/three-view/`）。
5. **建模**：FreeCAD headless runner（见 cad-freecad-ops 通道 A），env 传 `CAD_PARAMS`/`CAD_OUT`。
6. **校验**：`verify_stl.py` 三道自动门槛 + 3D Print Toolbox 壁厚人工确认；回传 dims/faces/volume 证据。
7. **确认门**：把 dims/证据回传用户，LOCKED 后进入切片（cad-verify → Bambu Studio）。

## 示例（已端到端验证）

`examples/three-view/` 台阶法兰：base_d=40/base_h=8/boss_d=24/boss_h=10/hole_d=10。
- `flange-3view.svg`：带尺寸标注的矢量三视图（文本可读）。
- `flange-3view-spec.md`：读图→参数对照表 + L0-L3 + 消歧说明。
- `flange-3view-params.json`：建模参数。
- 结果：dims=[40,40,18]mm / 6 精确 B-rep 面 / valid+closed / manifold_pass=true / STL 2748 面 AUTO_PASS。

## 避坑

- **病态性**：三视图≠唯一形体；无法判定时回确认门问用户，不要猜。
- **纯位图读图**：当前模型无图像输入，SVG/DXF 优先；位图请用户给尺寸表。
- **孔/凹特征**：视觉外壳路线会丢失；带尺寸工程图走参数化路线保留通孔。
- **单位**：工程图常标 mm；STL 无单位，默认 1 FreeCAD mm = 1 STL unit，导出前与用户确认。
- **比例**：SVG 示例为 4px/mm；读图时先确认图纸比例再换算。
- **DWG 不能直接读**：ezdxf 只吃 DXF；DWG 必须先用 AutoCAD accoreconsole / ODA / LibreCAD 转换，且版本兼容（AC1032 需 2018+ 转换器）。
- **标注层为空**：CAD 导出的三视图常把尺寸做成几何而非 DIMENSION 实体，需从实体坐标反推，别指望直接读出数字。
- **自由视图排布**：CAD 模型空间里三视图可能随意摆放（本例主/侧/俯分别在 x0-30 / x40-54 / y-35~-21），先定位各视图区域再映射，勿套固定三角布局。
- **孔/槽穿透性**：主/俯视隐藏线判断通孔 vs 盲孔、槽贯穿 vs 半透；无确凿证据时在 spec 记录假设并交确认门问用户。
