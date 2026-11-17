"""
参数化生成“莫比乌斯戒指”（半扭转实心带，水密可打印）。
用法: blender.exe --background --python mobius_ring.py
输出: output/mobius_A.stl ... + output/preview_A.png ... + 几何证据
"""
import bpy, math, os
from mathutils import Vector
import numpy as np

# Path independent: resolve output relative to this script unless CAD_OUT is set.
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
BASE = os.environ.get("CAD_BASE", os.path.dirname(SCRIPT_DIR))  # package root
OUT = os.environ.get("CAD_OUT") or os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)


def build_mobius(name, R, w, t, k=1, n=240):
    """半扭转实心带。R=中心圆半径, w=带宽, t=带厚, k=半扭转次数(奇数=莫比乌斯)。"""
    verts = []
    for i in range(n):
        theta = 2 * math.pi * i / n
        cx, cy, cz = R * math.cos(theta), R * math.sin(theta), 0.0
        N = np.array([math.cos(theta), math.sin(theta), 0.0])
        B = np.array([0.0, 0.0, 1.0])
        phi = k * theta / 2.0
        u = N * math.cos(phi) + B * math.sin(phi)
        v = -N * math.sin(phi) + B * math.cos(phi)
        corners = [(+1, +1), (-1, +1), (-1, -1), (+1, -1)]
        for s, r in corners:
            p = np.array([cx, cy, cz]) + s * (w / 2.0) * u + r * (t / 2.0) * v
            verts.append(tuple(p))

    faces = []
    for i in range(n):
        ni = (i + 1) % n
        off = 2 if ni == 0 and k % 2 == 1 else 0
        for j in range(4):
            a = i * 4 + j
            b = i * 4 + (j + 1) % 4
            c = ni * 4 + ((j + 1 + off) % 4)
            d = ni * 4 + ((j + off) % 4)
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    # 确定性修正法线朝向：保证闭合体体积为正（法线朝外，打印门槛）
    import bmesh as _bm
    _bmesh = _bm.new()
    _bmesh.from_mesh(mesh)
    if _bmesh.calc_volume(signed=True) < 0:
        _bm.ops.reverse_faces(_bmesh, faces=_bmesh.faces)
        _bmesh.to_mesh(mesh)
        mesh.update()
    _bmesh.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def check(obj):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    dims = tuple(round(x, 2) for x in obj.dimensions)
    return dims, len(obj.data.polygons), nonmanifold


def add_camera():
    bpy.ops.object.camera_add(location=(0, -30, 22))
    cam = bpy.context.object
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam


def render_preview(path):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
add_camera()

CANDIDATES = [
    ("A", dict(R=11.0, w=8.0, t=1.5, k=1)),
    ("B", dict(R=12.0, w=10.0, t=2.0, k=1)),
    ("C", dict(R=11.0, w=8.0, t=1.5, k=3)),
]

objs = []
for tag, params in CANDIDATES:
    obj = build_mobius(f"candidate_{tag}", **params)
    objs.append((tag, obj))

for tag, obj in objs:
    dims, nf, nm = check(obj)
    stl = os.path.join(OUT, f"mobius_{tag}.stl")
    png = os.path.join(OUT, f"preview_{tag}.png")
    for t2, o2 in objs:
        o2.hide_render = (o2 != obj)
    bpy.ops.wm.stl_export(filepath=stl, export_selected_objects=False, apply_modifiers=True)
    render_preview(png)
    print(f"RESULT {tag}: dims={dims} faces={nf} nonmanifold_edges={nm} stl={stl} png={png}")

print("DONE")
