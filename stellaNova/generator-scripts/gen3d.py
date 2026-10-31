"""Simple colored STEP bodies for parts that have no KiCad 3D model.

Coordinates are KiCad model space: X right, Y up (= footprint -y), Z up, mm,
origin at the footprint origin.
"""
import os, sys
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs

OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/v5dbg/project/3dmodels'
os.makedirs(OUT, exist_ok=True)


def box(x0, y0, z0, x1, y1, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()


def fp_box(fx0, fy0, fx1, fy1, z0, z1):
    """Box from footprint coords (y down) to model coords (y up)."""
    return box(fx0, -fy1, z0, fx1, -fy0, z1)


def write(name, parts):
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for shape, rgb in parts:
        lab = st.AddShape(shape, False)
        ct.SetColor(lab, Quantity_Color(rgb[0], rgb[1], rgb[2], Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    path = os.path.join(OUT, name + '.step')
    w.Write(path)
    return path


SILVER, BLACK, GOLD, GREY = (0.78, 0.79, 0.80), (0.08, 0.08, 0.09), (0.85, 0.68, 0.30), (0.35, 0.36, 0.38)

# Hirose DM3AT-SF-PEJM5 microSD, metal shell 14.0 x 15.8, 1.98 tall
shell = fp_box(-6.97, -7.88, 6.97, 7.9, 0, 1.98)
slot = fp_box(-5.6, 6.0, 5.6, 8.0, 0.25, 1.6)
dm3 = [(BRepAlgoAPI_Cut(shell, slot).Shape(), SILVER),
       (fp_box(-5.6, -8.2, 3.2, -7.2, 0, 0.25), GOLD)]
print(write('Hirose_DM3AT-SF-PEJM5', dm3))

# Molex 43202-4101 RJ9 jack, 11.18 wide x 18.03 deep x 11.58 tall, tab down
body = fp_box(-3.76, -3.8, 7.44, 14.3, 0, 11.58)
cav = fp_box(-2.1, 3.0, 5.91, 14.4, 2.2, 9.5)
rj = [(BRepAlgoAPI_Cut(body, cav).Shape(), BLACK),
      (fp_box(-1.4, 6.0, 5.2, 14.0, 8.9, 9.3), GOLD)]
print(write('Molex_43202-4101', rj))

# C&K PTS810: 4.2 x 3.2 x 1.6 body, 1.0 mm round actuator on top
base = fp_box(-2.1, -1.6, 2.1, 1.6, 0, 1.6)
act = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0, 0, 1.6), gp_Dir(0, 0, 1)), 0.85, 0.9).Shape()
pts = [(base, GREY), (act, BLACK)]
print(write('CK_PTS810', pts))

# Bel Fuse 0ZCG 1812 PTC: 4.5 x 3.2 x 0.75 body with tin end caps
ptc = [(fp_box(-1.75, -1.6, 1.75, 1.6, 0, 0.75), (0.16, 0.30, 0.48)),
       (fp_box(-2.25, -1.6, -1.75, 1.6, 0, 0.75), SILVER), (fp_box(1.75, -1.6, 2.25, 1.6, 0, 0.75), SILVER)]
print(write('BelFuse_0ZCG_1812', ptc))
