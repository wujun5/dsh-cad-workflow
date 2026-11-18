# -*- coding: utf-8 -*-
"""Render an STL to a 3D preview PNG (isometric) with matplotlib."""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

stl = sys.argv[1]
out = sys.argv[2]
mesh = trimesh.load(stl, process=True)

fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection="3d")
verts = np.asarray(mesh.vertices)
faces = np.asarray(mesh.faces)
# light shading by face normal (face_normals is a computed property in trimesh 5.x)
nrm = np.asarray(mesh.face_normals)
light = np.array([0.3, -0.5, 0.8]); light = light / np.linalg.norm(light)
shade = np.clip(np.abs(nrm @ light), 0.25, 1.0)
cols = np.zeros((len(faces), 4))
cols[:, 0] = 0.55 * shade
cols[:, 1] = 0.62 * shade
cols[:, 2] = 0.72 * shade
cols[:, 3] = 1.0
polys = verts[faces]
pc = Poly3DCollection(polys, facecolors=cols, edgecolors="none", linewidths=0)
ax.add_collection3d(pc)

allv = verts
ax.set_xlim(allv[:, 0].min(), allv[:, 0].max())
ax.set_ylim(allv[:, 1].min(), allv[:, 1].max())
ax.set_zlim(allv[:, 2].min(), allv[:, 2].max())
ax.set_box_aspect((np.ptp(allv[:, 0]), np.ptp(allv[:, 1]), np.ptp(allv[:, 2])))
ax.view_init(elev=24, azim=-60)
ax.set_xlabel("X width (mm)"); ax.set_ylabel("Y depth (mm)"); ax.set_zlabel("Z height (mm)")
ax.set_title("Reverse-engineered from part.dwg three views")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("SAVED", out)
