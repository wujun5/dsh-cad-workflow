"""
莫比乌斯环 —— FreeCAD headless B-rep 代码即模型路线（通道 A）。
用法(环境变量传参, 避开 FreeCADCmd 对中文 GBK 解码):
  $env:CAD_R="11"; $env:CAD_W="8"; $env:CAD_T="1.5"; $env:CAD_K="2"; $env:CAD_N="60"; $env:CAD_OUT="..."
  FreeCADCmd.exe build_mobius_freecad.py
几何: 沿中心圆扫掠矩形截面, 每步扭转 phi = k*theta/2。
  k=1  -> 经典莫比乌斯(180度扭转, 首尾错位, 需 off=2 缝合网格)
  k=2  -> 360度扭转 (首尾同向真正闭合)  => 真正水密可打印实体 (本脚本默认)
输出: mobius_freecad.stl / .step / .build-evidence.json
"""
import FreeCAD as App
import Part
import math
import os
import json
import traceback

# Path independent: resolve output relative to this script unless CAD_OUT is set.
# FreeCADCmd runs scripts via exec, so __file__ may be absent -> fall back to cwd.
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
BASE = os.environ.get("CAD_BASE", os.path.dirname(SCRIPT_DIR))  # package root
OUT = os.environ.get("CAD_OUT") or os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

R = float(os.environ.get("CAD_R", "11.0"))
w = float(os.environ.get("CAD_W", "8.0"))
t = float(os.environ.get("CAD_T", "1.5"))
k = int(os.environ.get("CAD_K", "2"))   # 默认双周期闭合(360度)
n = int(os.environ.get("CAD_N", "60"))  # loft 截面数


def wire_at(theta):
    cx, cy, cz = R * math.cos(theta), R * math.sin(theta), 0.0
    N = App.Vector(math.cos(theta), math.sin(theta), 0)
    B = App.Vector(0, 0, 1)
    phi = k * theta / 2.0
    u = N * math.cos(phi) + B * math.sin(phi)
    v = N * (-math.sin(phi)) + B * math.cos(phi)
    C = App.Vector(cx, cy, cz)
    corners = []
    for s, r in [(+1, +1), (-1, +1), (-1, -1), (+1, -1)]:
        corners.append(C + u * (s * w / 2.0) + v * (r * t / 2.0))
    corners.append(corners[0])
    return Part.makePolygon(corners)


def main():
    wires = [wire_at(2 * math.pi * i / n) for i in range(n)]
    # 闭合 loft: solid=True, ruled=False, closed=True
    shape = Part.makeLoft(wires, True, False, True)
    valid = shape.isValid()
    closed = shape.isClosed()
    solids = len(shape.Solids)
    faces = len(shape.Faces)
    vol = round(shape.Volume, 3)
    bb = shape.BoundBox
    dims = [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)]
    manifold = valid and closed and solids == 1

    stl = os.path.join(OUT, "mobius_freecad.stl")
    step = os.path.join(OUT, "mobius_freecad.step")
    shape.exportStl(stl)
    shape.exportStep(step)

    ev = {
        "engine": "FreeCAD", "channel": "headless-code(B-rep)",
        "params": {"R": R, "w": w, "t": t, "k": k, "n": n},
        "dims_mm": dims, "valid": valid, "closed": closed, "solids": solids,
        "faces": faces, "volume_mm3": vol, "manifold_pass": manifold,
        "stl": stl, "step": step,
        "stl_bytes": os.path.getsize(stl), "step_bytes": os.path.getsize(step),
    }
    with open(os.path.join(OUT, "mobius_freecad.build-evidence.json"), "w", encoding="utf-8") as f:
        json.dump(ev, f, ensure_ascii=False, indent=2)
    print("FREECAD_MOBIUS_RESULT=" + json.dumps(ev, ensure_ascii=False))


try:
    main()
except Exception:
    traceback.print_exc()
    raise
