# -*- coding: utf-8 -*-
"""Render the three-view DXF geometry to a preview PNG using matplotlib."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ezdxf

path = sys.argv[1]
out = sys.argv[2]
doc = ezdxf.readfile(path)
msp = doc.modelspace()

fig, ax = plt.subplots(figsize=(12, 10))
colors = {"Outlines": "black", "Hidden": "red", "Centerlines": "blue", "Dimensions": "green"}
for e in msp:
    lay = e.dxf.layer
    col = colors.get(lay, "gray")
    t = e.dxftype()
    if t == "LINE":
        s, en = e.dxf.start, e.dxf.end
        ax.plot([s.x, en.x], [s.y, en.y], color=col, lw=1.5)
    elif t == "CIRCLE":
        c = e.dxf.center
        circ = plt.Circle((c.x, c.y), e.dxf.radius, fill=False, color=col, lw=1.5)
        ax.add_patch(circ)
    elif t == "ARC":
        c = e.dxf.center
        import numpy as np
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        if a1 < a0: a1 += 360
        ang = np.linspace(a0, a1, 50)
        xs = c.x + e.dxf.radius * np.cos(np.deg2rad(ang))
        ys = c.y + e.dxf.radius * np.sin(np.deg2rad(ang))
        ax.plot(xs, ys, color=col, lw=1.5)
ax.set_aspect("equal")
ax.set_xlim(-5, 58)
ax.set_ylim(-42, 28)
ax.set_title("Three-view drawing (black=outline, red=hidden, blue=center)")
ax.grid(True, alpha=0.3)
fig.savefig(out, dpi=150, bbox_inches="tight")
print("SAVED", out)
