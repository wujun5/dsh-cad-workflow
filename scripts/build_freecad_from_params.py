"""
FreeCAD headless "spec -> B-rep solid -> STL" runner (superior route for functional parts).

WHY THIS ROUTE (over MCP live channel):
  - No GUI, no RPC server, no socket: runs via FreeCADCmd.exe as a plain process.
  - True OCCT B-rep solids (exact geometry), exportable to STEP as well as STL.
  - Deterministic, reproducible, batch-friendly, CI-friendly: params.json IS the model.
  - MCP execute_code_headless uses this same mechanism under the hood.

Usage (IMPORTANT - pass paths via env vars, NOT as CLI args):
  $env:CAD_PARAMS = "<params.json>"; $env:CAD_OUT = "<out_dir>"
  "D:\\Program Files\\FreeCAD 27.1\\bin\\FreeCADCmd.exe" build_freecad_from_params.py

WHY ENV VARS: FreeCADCmd tries to process EVERY CLI argument as a file. Passing a
params.json (esp. one with non-ASCII comments) as an arg makes FreeCAD open it
with the default GBK codec and fail. Env vars keep the script the only file arg.
Also supports `-- <params.json> <out_dir>` for parity, but env vars are preferred.

Reads a params.json (same schema as build_from_params.py), builds the shape with
Part primitives, checks solid validity / watertightness / volume, exports STL +
STEP, and writes a JSON evidence file. Units: numeric mm (1 FreeCAD mm = 1 STL unit).
"""
import sys
import os
import json
import math

import FreeCAD as App
import Part


def parse_args():
    # Prefer environment variables (robust against FreeCADCmd arg processing).
    params_path = os.environ.get("CAD_PARAMS")
    out_dir = os.environ.get("CAD_OUT")
    if params_path:
        return params_path, out_dir
    # Fallback: -- <params.json> <out_dir>
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
        params_path = argv[0] if len(argv) > 0 else None
        out_dir = out_dir or (argv[1] if len(argv) > 1 else None)
        return params_path, out_dir
    return None, None


def build_shape(shape, p):
    """Return a Part.Shape (B-rep solid)."""
    if shape == "washer":
        outer = float(p["outer_d"])
        hole = float(p["hole_d"])
        thick = float(p["thickness"])
        base = Part.makeCylinder(outer / 2.0, thick, App.Vector(0, 0, 0))
        cutter = Part.makeCylinder(hole / 2.0, thick * 3, App.Vector(0, 0, -thick))
        return base.cut(cutter).removeSplitter()

    if shape == "cylinder":
        dia = float(p.get("diameter", p.get("outer_d")))
        h = float(p.get("height", p.get("thickness")))
        return Part.makeCylinder(dia / 2.0, h, App.Vector(0, 0, 0))

    if shape == "box":
        l = float(p["length"])
        w = float(p["width"])
        h = float(p["height"])
        return Part.makeBox(l, w, h, App.Vector(0, 0, 0))

    raise ValueError("unsupported shape: %r" % shape)


def shape_evidence(shape):
    bb = shape.BoundBox
    return {
        "dimensions_mm": [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
        "is_valid": bool(shape.isValid()),
        "is_closed": bool(shape.isClosed()),
        "solids": len(shape.Solids),
        "faces": len(shape.Faces),
        "volume_mm3": round(shape.Volume, 3),
    }


def main():
    params_path, out_dir = parse_args()
    if not params_path:
        raise SystemExit("usage: build_freecad_from_params.py -- <params.json> <out_dir>")
    with open(params_path, "r", encoding="utf-8-sig") as f:
        spec = json.load(f)

    if not out_dir:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(params_path)), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    shape = spec.get("shape", "washer")
    p = spec.get("params", {})
    stem = spec.get("_spec", "part").replace(".md", "")

    solid = build_shape(shape, p)
    ev = shape_evidence(solid)

    stl_path = os.path.join(out_dir, stem + "-freecad.stl")
    step_path = os.path.join(out_dir, stem + "-freecad.step")
    solid.exportStl(stl_path)
    solid.exportStep(step_path)

    evidence = {
        "spec": spec.get("_spec"),
        "shape": shape,
        "engine": "freecad",
        "freecad_version": ".".join(App.Version()[:3]),
        "kernel": "OCCT B-rep (exact)",
        "params": p,
        "shape_evidence": ev,
        "stl_path": stl_path,
        "step_path": step_path,
        "manifold_pass": ev["is_valid"] and ev["is_closed"] and ev["solids"] == 1 and ev["volume_mm3"] > 0,
    }
    ev_path = os.path.join(out_dir, stem + "-freecad.build-evidence.json")
    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=2)

    print("BUILD_EVIDENCE " + json.dumps(evidence, ensure_ascii=False))
    print("DONE")


# FreeCADCmd executes scripts via exec with __name__ != "__main__", so call
# main() unconditionally. Only skip when imported as a normal module by name
# containing 'build_freecad_from_params' is not detectable here, so this file
# is a dedicated runner: always run.
main()
