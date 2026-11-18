# -*- coding: utf-8 -*-
"""Inspect a DXF: layouts, layers, entity type counts, and geometry details."""
import sys
import ezdxf
from ezdxf import bbox

path = sys.argv[1]
doc = ezdxf.readfile(path)
print("DXF_VERSION", doc.dxfversion)
print("INSUNITS", doc.header.get("$INSUNITS", "?"))
print("MEASUREMENT", doc.header.get("$MEASUREMENT", "?"))
print("EXTMIN", doc.header.get("$EXTMIN", "?"))
print("EXTMAX", doc.header.get("$EXTMAX", "?"))

print("\n=== LAYERS ===")
for lay in doc.layers:
    print("LAYER", repr(lay.dxf.name), "color", lay.dxf.color)

print("\n=== BLOCKS (non-model) ===")
for blk in doc.blocks:
    if blk.name.startswith("*"):
        continue
    print("BLOCK", repr(blk.name), "entities", len(list(blk)))

for layout_name in ["Model", "Layout1", "Layout2"]:
    try:
        layout = doc.layout(layout_name)
    except Exception:
        continue
    ents = list(layout)
    print("\n=== LAYOUT %r : %d entities ===" % (layout_name, len(ents)))
    from collections import Counter
    c = Counter(e.dxftype() for e in ents)
    print("TYPE_COUNTS", dict(c))
    for i, e in enumerate(ents):
        t = e.dxftype()
        layer = e.dxf.layer
        if t == "LINE":
            s = e.dxf.start; en = e.dxf.end
            print("  LINE[%d] layer=%s (%.3f,%.3f)->(%.3f,%.3f)" % (i, layer, s.x, s.y, en.x, en.y))
        elif t == "CIRCLE":
            cc = e.dxf.center
            print("  CIRCLE[%d] layer=%s c=(%.3f,%.3f) r=%.3f" % (i, layer, cc.x, cc.y, e.dxf.radius))
        elif t == "ARC":
            cc = e.dxf.center
            print("  ARC[%d] layer=%s c=(%.3f,%.3f) r=%.3f a=(%.1f,%.1f)" % (i, layer, cc.x, cc.y, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle))
        elif t in ("LWPOLYLINE", "POLYLINE"):
            pts = []
            if t == "LWPOLYLINE":
                pts = [(round(p[0], 3), round(p[1], 3)) for p in e.get_points()]
            print("  %s[%d] layer=%s closed=%s pts=%s" % (t, i, layer, getattr(e, "closed", "?"), pts[:20]))
        elif t == "TEXT":
            print("  TEXT[%d] layer=%s %r at=(%.3f,%.3f) h=%.3f" % (i, layer, e.dxf.text, e.dxf.insert.x, e.dxf.insert.y, e.dxf.height))
        elif t == "MTEXT":
            print("  MTEXT[%d] layer=%s %r" % (i, layer, e.text[:200]))
        elif t == "DIMENSION":
            print("  DIMENSION[%d] layer=%s text=%r type=%s" % (i, layer, e.dxf.get("text", "<>"), e.dxf.dimtype))
        elif t == "INSERT":
            print("  INSERT[%d] layer=%s name=%r at=(%.3f,%.3f)" % (i, layer, e.dxf.name, e.dxf.insert.x, e.dxf.insert.y))
        elif t == "SOLID" or t == "3DFACE":
            print("  %s[%d] layer=%s" % (t, i, layer))
        else:
            print("  %s[%d] layer=%s" % (t, i, layer))
