# DWG 三视图逆向案例（part.dwg）

从真实 AutoCAD 三视图逆向出可打印 3D 的完整可复用案例。完整讲解见 `docs/DWG三视图逆向实战.md`。

## 文件

| 文件 | 用途 |
|---|---|
| `dwg2dxf.scr` | AutoCAD accoreconsole 无 GUI 转换脚本；`__OUT_DXF__` 占位符需替换为目标 dxf 绝对路径 |
| `parse_dxf.py` | ezdxf 解析 DXF：图层/实体类型/坐标/单位 → 用于反推尺寸 |
| `plot_views.py` | 把 DXF 三视图渲染成 PNG（需 matplotlib） |
| `render_preview.py` | 把生成的 STL 渲染成 3D 预览 PNG（需 trimesh+matplotlib） |
| `project_check.py` | 把 STL 三向投影，逐视图比对包围盒是否等于 DXF 反推尺寸 |
| `part-spec.md` | 读图记录：实体坐标→尺寸对照 + 交叉校验 + 消歧 |
| `part-params.json` | 建模参数（shape=grooved_bracket） |

## 用法（Windows，路径无关）

```powershell
# 1) 版本探测：读 DWG 前 6 字节，AC1032=AutoCAD 2018
$dwg = 'D:\path\to\input.dwg'
$dxf = 'D:\path\to\output.dxf'

# 2) DWG -> DXF（先替换脚本里的 __OUT_DXF__ 为 $dxf）
$scr = Get-Content .\dwg2dxf.scr -Raw
$scr = $scr.Replace('__OUT_DXF__', $dxf)
Set-Content -Path .\dwg2dxf.rendered.scr -Value $scr -Encoding ASCII
& 'D:\Program Files\AutoCAD\AutoCAD 2026\accoreconsole.exe' /i $dwg /s .\dwg2dxf.rendered.scr

# 3) 解析 DXF（反推尺寸）
& 'D:\Program Files\anaconda3\python.exe' .\parse_dxf.py $dxf

# 4) 读尺寸后写 params.json，建模（见 cad-freecad-ops 通道 A）
$env:CAD_PARAMS = '<path>\part-params.json'
$env:CAD_OUT    = '<out dir>'
& 'D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe' '<pkg>\scripts\build_freecad_from_params.py'

# 5) 校验：三道门槛 + 三向投影自检
& 'D:\Program Files\anaconda3\python.exe' '<pkg>\scripts\verify_stl.py' '<out>\part-spec-freecad.stl'
& 'D:\Program Files\anaconda3\python.exe' .\project_check.py '<out>\part-spec-freecad.stl'
```

## 边界

- 标注层常为空，尺寸靠实体坐标反推；孔/槽穿透性属投影推断，需看预览图或问用户确认。
- 三视图是病态问题：仅回转体/基本体叠加可唯一重建；斜面/相贯线/非对称切除需补信息。
- 无 AutoCAD 时用 ODA File Converter / LibreCAD / QCAD 转 DXF。
