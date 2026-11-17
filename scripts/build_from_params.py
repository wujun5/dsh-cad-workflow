"""
Generic headless "spec -> geometry" runner (L2 fallback bridge, no GUI/MCP needed).

Usage:
  blender.exe --background --python build_from_params.py -- <params.json> <out_dir>

Reads a params.json (see examples/example-params.json), builds the requested
shape with bpy, checks manifold, exports STL, and writes a JSON evidence file.

Supported params["shape"]:
  washer   : outer cylinder minus central hole  -> needs params.outer_d/hole_d/thickness
  cylinder : solid cylinder                      -> needs params.diameter/height (or outer_d/thickness)
  box      : rectangular block                    -> needs params.length/width/height

Note: Blender units are metres by convention, but STL is unitless and slicers
interpret numbers as mm. We model with numeric mm values directly (1 unit = 1 mm
in the exported mesh), matching the rest of this workflow.
"""
import bpy
import bmesh
import json
import os
import sys


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    params_path = argv[0] if len(argv) > 0 else None
    out_dir = argv[1] if len(argv) > 1 else None
    return params_path, out_dir


def mesh_evidence(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    volume = bm.calc_volume(signed=True)
    bm.free()
    return {
        "dimensions_mm": [round(v, 3) for v in obj.dimensions],
        "faces": len(obj.data.polygons),
        "vertices": len(obj.data.vertices),
        "nonmanifold_edges": nonmanifold,
        "signed_volume": round(volume, 3),
    }


def build_shape(shape, p):
    if shape == "washer":
        outer = p["outer_d"]
        hole = p["hole_d"]
        thick = p["thickness"]
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=outer / 2.0, depth=thick, location=(0, 0, thick / 2.0))
        base = bpy.context.object
        base.name = "P01_washer"
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=hole / 2.0, depth=thick * 3, location=(0, 0, thick / 2.0))
        cutter = bpy.context.object
        bpy.context.view_layer.objects.active = base
        mod = base.modifiers.new("center_hole", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        return base

    if shape == "cylinder":
        dia = p.get("diameter", p.get("outer_d"))
        h = p.get("height", p.get("thickness"))
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=dia / 2.0, depth=h, location=(0, 0, h / 2.0))
        obj = bpy.context.object
        obj.name = "P01_cylinder"
        return obj

    if shape == "box":
        l = p["length"]
        w = p["width"]
        h = p["height"]
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h / 2.0))
        obj = bpy.context.object
        obj.name = "P01_box"
        obj.scale = (l, w, h)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return obj

    raise ValueError("unsupported shape: %r" % shape)


def main():
    params_path, out_dir = parse_args()
    if not params_path:
        raise SystemExit("usage: build_from_params.py -- <params.json> <out_dir>")
    with open(params_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    if not out_dir:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(params_path)), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    shape = spec.get("shape", "washer")
    p = spec.get("params", {})

    # clean scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    obj = build_shape(shape, p)
    # store params as custom properties (Blender's substitute for a parametric tree)
    for k, v in p.items():
        try:
            obj[k] = v
        except Exception:
            pass

    ev = mesh_evidence(obj)
    # deterministically fix inward normals
    if ev["signed_volume"] < 0:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        ev = mesh_evidence(obj)

    stem = spec.get("_spec", "part").replace(".md", "")
    stl_path = os.path.join(out_dir, stem + ".stl")
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=False, apply_modifiers=True)

    evidence = {
        "spec": spec.get("_spec"),
        "shape": shape,
        "engine": "blender",
        "blender_version": bpy.app.version_string,
        "params": p,
        "mesh_evidence": ev,
        "stl_path": stl_path,
        "manifold_pass": ev["nonmanifold_edges"] == 0 and ev["signed_volume"] > 0,
    }
    ev_path = os.path.join(out_dir, stem + ".build-evidence.json")
    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=2)

    print("BUILD_EVIDENCE " + json.dumps(evidence, ensure_ascii=False))
    print("DONE")


if __name__ == "__main__":
    main()
