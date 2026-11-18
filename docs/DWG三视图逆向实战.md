# 真实 CAD 三视图逆向实战（part.dwg → 3D）

2026-11-18 实测：从用户提供的真实 AutoCAD 文件逆向出可打印 3D 模型。这是比 SVG 示例更接近日常场景的案例——拿到一个 `.dwg` 三视图文件，逆向为 3D。

## 工具链（本机实测）

| 环节 | 工具 | 说明 |
|---|---|---|
| DWG 版本探测 | 读文件头 6 字节 | `AC1032` = AutoCAD 2018 |
| DWG → DXF | AutoCAD 2026 `accoreconsole.exe`（无 GUI 核心控制台） | ezdxf 不能直接读 DWG，必须先转 DXF |
| DXF 解析 | ezdxf 1.4.5（anaconda） | 读图层/实体/坐标/单位 |
| 建模 | FreeCAD headless `build_freecad_from_params.py`（新增 `grooved_bracket`） | OCCT B-rep 精确实体 |
| 校验 | `verify_stl.py`（trimesh）+ 三向投影自检 | 水密/法线/体积 + 视图尺寸吻合 |

## 步骤

### 1. 探测版本
`part.dwg` 前 6 字节 = `AC1032`（AutoCAD 2018），16.6 KB。

### 2. DWG → DXF
无 GUI 转换脚本 `dwg2dxf.scr`：
```
FILEDIA
0
_.DXFOUT
<out.dxf>
16
_.QUIT
_Y
```
命令：`accoreconsole.exe /i part.dwg /s dwg2dxf.scr` → 得 `part.dxf`（R2018 ASCII，80 KB）。
- 16 = 2018 格式版本号（DXFOUT 提示可选 0–16，对应 R12–R2018）。
- 没有 AutoCAD 时用 ODA File Converter 或 LibreCAD/QCAD 转换。

### 3. 解析实体
ezdxf 读 modelspace：30 实体（27 LINE / 1 ARC / 2 CIRCLE）。图层语义：
- `Outlines` 实线轮廓 / `Hidden` 虚线（孔、槽底）/ `Centerlines` 中心线 / `Dimensions` 标注层**为空**。
- `$INSUNITS=6`（mm）、`$MEASUREMENT=1`（公制）。
- 三视图是**自由排布**（非标准三角配置）：主视 x0–30/y0–22、侧视 x40–54/y0–22、俯视 x0–30/y−35…−21。

### 4. 反推尺寸（标注层为空，从坐标反推）
| 参数 | 来源 | 值(mm) |
|---|---|---|
| width | 主视底座宽 x0→30 | 30 |
| base_depth | 侧视底座深 40→54 / 俯视 y−35→−21 | 14 |
| base_height | 主视底座高 y0→8 | 8 |
| upright_depth | 侧视立板深 40→48 / 俯视 −29→−21 | 8 |
| upright_height | 主视顶高 22−8 | 14 |
| groove_radius | 主视 ARC 中心(15,22) R10 | 10 |
| hole_diameter | 俯视 CIRCLE R4 | 8 |
| hole_x1/x2 | 主/俯视孔心 x7.5 / 22.5 | 7.5 / 22.5 |
| hole_y | 俯视孔心深向 −28（距前边 7=深/2） | 7 |

交叉校验：总高 22=8+14 ✓；槽底 22−R10=12=侧视隐藏线 y12 ✓；立板深 8 两侧一致 ✓；孔位 x 主/俯一致 ✓；孔径 R4→Ø8、主视隐藏线间距 15=7.5+7.5 ✓。

### 5. 消歧判定
- 非回转体，但为**基本体叠加 + 定向切除**，三视图信息充分 → 可唯一重建。
- 孔判竖直通孔（贯穿底座 8）；槽判沿深度贯穿立板——基于隐藏线投影证据，假设记录于 spec，交确认门。

### 6. 建模 + 校验
```
$env:CAD_PARAMS = '<out>\part-params.json'
$env:CAD_OUT    = '<out>'
& 'D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe' '<pkg>\scripts\build_freecad_from_params.py'
& 'D:\Program Files\anaconda3\python.exe' '<pkg>\scripts\verify_stl.py' '<out>\part-spec-freecad.stl'
```

## 实测结果

| 项 | 值 |
|---|---|
| B-rep dims | [30, 14, 22] mm（与三视图总高/宽/深完全吻合）|
| B-rep faces | 14（精确解析面）|
| valid/closed/solids | true / true / 1 |
| volume | 4659.115 mm³ |
| manifold_pass | true |
| STL | 2328 面，watertight + winding + volume 全过 → **AUTO_PASS** |
| 三向投影自检 | FRONT/SIDE/TOP 包围盒全部吻合 → ALL_VIEWS_MATCH=True |
| 产物 | `part-spec-freecad.stl` / `.step` / `.build-evidence.json` / `part-model-preview.png` |

## 结论与边界

- **真实 CAD DWG 三视图 → 可打印 3D 已跑通**：靠"转 DXF + 解析实体坐标 + 反推尺寸 + 参数化建模"，而非一键转换。
- 全程无需图像识别（当前模型不支持图像输入），靠矢量实体坐标，结果可审计。
- 边界：标注层为空时尺寸靠反推；孔/槽的穿透性属投影推断，需看预览图或问用户确认；若图纸含斜面/相贯线/非对称切除，三视图不足以唯一确定。

## 复用脚本

本案例的辅助脚本在 `_cad_workflow/output/`（dwg2dxf.scr / parse_dxf.py / plot_views.py / render_preview.py / project_check.py），可复制改造用于其它 DWG 三视图逆向。
