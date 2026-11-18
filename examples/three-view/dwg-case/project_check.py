# -*- coding: utf-8 -*-
"""Project the 3D model's silhouette onto 3 planes and compare extents to the DXF views."""
import sys
import numpy as np
import trimesh

mesh = trimesh.load(sys.argv[1], process=True)
v = np.asarray(mesh.vertices)
print("MODEL extents X/Y/Z:", [round(float(x), 3) for x in mesh.extents])

# For each view, report the 2D bounding box of all vertices.
def proj(name, a, b):
    print("%s: %s range [%.2f, %.2f], %s range [%.2f, %.2f]" % (
        name, a, v[:, a].min(), v[:, a].max(), b, v[:, b].min(), v[:, b].max()))

proj("FRONT (X=width, Z=height)", 0, 2)
proj("SIDE  (Y=depth, Z=height)", 1, 2)
proj("TOP   (X=width, Y=depth)", 0, 1)

# Expected from DXF reverse-engineering:
# FRONT: X 0..30, Z 0..22 ; SIDE: Y 0..14, Z 0..22 ; TOP: X 0..30, Y 0..14
exp = {
    "FRONT": (0, 30, 0, 22),
    "SIDE": (0, 14, 0, 22),
    "TOP": (0, 30, 0, 14),
}
actual = {
    "FRONT": (v[:,0].min(), v[:,0].max(), v[:,2].min(), v[:,2].max()),
    "SIDE": (v[:,1].min(), v[:,1].max(), v[:,2].min(), v[:,2].max()),
    "TOP": (v[:,0].min(), v[:,0].max(), v[:,1].min(), v[:,1].max()),
}
print("\n=== comparison to DXF-derived dims ===")
allok = True
for k in exp:
    ok = all(abs(a - b) < 0.05 for a, b in zip(exp[k], actual[k]))
    allok &= ok
    print("%s expected %s actual %s -> %s" % (k, exp[k], tuple(round(x,2) for x in actual[k]), "OK" if ok else "MISMATCH"))
print("ALL_VIEWS_MATCH =", allok)
