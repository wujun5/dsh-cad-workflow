"""
Verify printability of an STL with trimesh.

Three gates are auto-verifiable from a closed triangle mesh:
  1. watertight           (is_watertight)
  2. winding / normals    (is_winding_consistent, volume > 0)
  3. (signed volume > 0)

Wall thickness is NOT reliably auto-verifiable from a triangle soup: a nearest
vertex distance measures mesh edge length, not the physical wall. Thin-wall
checking is therefore reported as a MANUAL check (use Blender 3D Print Toolbox
-> Check All -> Thin Walls), never as a fabricated pass/fail.

Usage:
  python verify_stl.py <model.stl> [min_wall_mm]
"""
import json
import sys
import trimesh


def verify(path, min_wall=0.4):
    # STL stores each triangle with independent (duplicated) vertices. Loading
    # with process=False keeps those duplicates and makes is_watertight report
    # False even for a perfectly closed solid, so merge them first.
    mesh = trimesh.load(path, process=True)
    if hasattr(mesh, "merge_vertices"):
        mesh.merge_vertices()

    watertight = bool(mesh.is_watertight)
    winding = bool(mesh.is_winding_consistent)
    volume = round(float(mesh.volume), 3)
    extents = [round(float(v), 3) for v in mesh.extents]

    auto_gates = {
        "watertight": watertight,
        "winding_consistent": winding,
        "volume_positive": volume > 0,
    }
    auto_pass = all(auto_gates.values())

    result = {
        "file": path,
        "faces": len(mesh.faces),
        "vertices": len(mesh.vertices),
        "watertight": watertight,
        "winding_consistent": winding,
        "volume": volume,
        "bounds_mm": extents,
        "auto_gates": auto_gates,
        "manual_checks": [
            {
                "gate": "min_wall_thickness",
                "required_mm": min_wall,
                "status": "MANUAL_REQUIRED",
                "how": "Blender > N panel > 3D Print Toolbox > Check All > Thin Walls.",
            }
        ],
        "verdict": "AUTO_PASS" if auto_pass else "FAIL",
        "note": "Auto verdict covers watertightness/normals only; wall thickness must be checked manually before slicing.",
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python verify_stl.py <model.stl> [min_wall_mm]")
    min_wall = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
    print(json.dumps(verify(sys.argv[1], min_wall), ensure_ascii=False, indent=2))
