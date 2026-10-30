"""Render the board in 3D: STEP models with colors, plus copper/mask/silk texture on both faces.

python3 render3d.py <board.kicad_pcb> <board.step> <out_prefix> [views...]
Run under xvfb-run.
"""
import sys, os, re, subprocess, tempfile
import numpy as np
from PIL import Image
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.XCAFPrs import XCAFPrs, XCAFPrs_DocumentExplorer, XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes
from OCP.OCP.collections import IndexedDataMap_TopoDS_Shape_XCAFPrs_Style_TopTools_ShapeMapHasher as StyleMap
from OCP.TCollection import TCollection_ExtendedString
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.IFSelect import IFSelect_RetDone
import pyvista as pv

pcb, step, out = sys.argv[1], sys.argv[2], sys.argv[3]
views = sys.argv[4:] or ['iso', 'top', 'bottom']
PX = 40  # texture pixels per mm

# ---------------------------------------------------------------- texture
def layer_mask(layer, tmp):
    svg = os.path.join(tmp, layer + '.svg'); png = os.path.join(tmp, layer + '.png')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '-l', f'{layer},Edge.Cuts', '--page-size-mode', '2',
                    '--exclude-drawing-sheet', '--black-and-white', '-o', svg, pcb], capture_output=True, check=True)
    head = open(svg).read(4000)
    wmm = float(re.search(r'width="([\d.]+)mm"', head).group(1)); hmm = float(re.search(r'height="([\d.]+)mm"', head).group(1))
    subprocess.run(['rsvg-convert', '-w', str(int(wmm * PX)), '-h', str(int(hmm * PX)), svg, '-o', png], check=True)
    a = np.array(Image.open(png).convert('RGBA')).astype(float)
    return a[..., 3] / 255.0, svg

def edge_rect(svg):
    s = open(svg).read()
    nums = []
    for d in re.findall(r'<path[^>]*d="([^"]+)"', s):
        nums += [float(v) for v in re.findall(r'-?\d+\.?\d*', d)]
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)

def textures():
    tmp = tempfile.mkdtemp()
    edge, esvg = layer_mask('Edge.Cuts', tmp)
    ys, xs = np.nonzero(edge > 0.3)
    lw = int(round(0.05 * PX))   # half the 0.1 mm outline width
    crop = (int(xs.min()) + lw, int(ys.min()) + lw, int(xs.max()) - lw + 1, int(ys.max()) - lw + 1)
    res = {}
    for side, cu, mask, silk in (('top', 'F.Cu', 'F.Mask', 'F.Silkscreen'), ('bottom', 'B.Cu', 'B.Mask', 'B.Silkscreen')):
        C = np.clip(layer_mask(cu, tmp)[0] - edge, 0, 1)
        M = np.clip(layer_mask(mask, tmp)[0] - edge, 0, 1)
        S = np.clip(layer_mask(silk, tmp)[0] - edge, 0, 1)
        img = np.zeros(C.shape + (3,)); img[:] = (0.07, 0.30, 0.16)          # soldermask over bare FR4
        img = img * (1 - C[..., None]) + np.array((0.15, 0.44, 0.23)) * C[..., None]   # copper under mask
        gold, fr4 = np.array((0.88, 0.72, 0.38)), np.array((0.70, 0.60, 0.38))
        bare = gold * C[..., None] + fr4 * (1 - C[..., None])
        img = img * (1 - M[..., None]) + bare * M[..., None]
        sv = (S * (1 - M))[..., None]
        img = img * (1 - sv) + np.array((0.95, 0.95, 0.92)) * sv
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).crop(crop)
        p = f'{out}-tex-{side}.png'; im.save(p); res[side] = p
    return res

tex = textures()

# ---------------------------------------------------------------- STEP
doc = TDocStd_Document(TCollection_ExtendedString('doc'))
rd = STEPCAFControl_Reader(); rd.SetColorMode(True); rd.SetNameMode(True)
assert rd.ReadFile(step) == IFSelect_RetDone
rd.Transfer(doc)

meshes = []
board_bounds = None

def mesh_faces(shape, face_rgb, default):
    BRepMesh_IncrementalMesh(shape, 0.04, False, 0.3, True)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        f = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None:
            tr = loc.Transformation()
            pts = np.array([[*tri.Node(i).Transformed(tr).Coord()] for i in range(1, tri.NbNodes() + 1)])
            rev = f.Orientation() == TopAbs_REVERSED
            fl = []
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                fl.append((3, a - 1, c - 1, b - 1) if rev else (3, a - 1, b - 1, c - 1))
            col = default
            for key, rgb in face_rgb:
                if key.IsPartner(f):
                    col = rgb; break
            meshes.append((pts, np.array(fl).ravel(), col))
        exp.Next()

ex = XCAFPrs_DocumentExplorer(doc, XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes)
while ex.More():
    node = ex.Current()
    base = XCAFDoc_ShapeTool.GetShape_s(node.RefLabel)
    shape = base.Moved(node.Location)
    sm = StyleMap()
    XCAFPrs.CollectStyleSettings_s(node.RefLabel, TopLoc_Location(), sm)
    default = (0.5, 0.5, 0.5)
    st = node.Style
    if st.IsSetColorSurf():
        c = st.GetColorSurf(); default = (c.Red(), c.Green(), c.Blue())
    face_rgb = []
    for i in range(1, sm.Size() + 1):
        k, s2 = sm.FindKey(i), sm.FindFromIndex(i)
        if s2.IsSetColorSurf():
            c = s2.GetColorSurf(); rgb = (c.Red(), c.Green(), c.Blue())
            if k.IsPartner(base):
                default = rgb
            else:
                e2 = TopExp_Explorer(k, TopAbs_FACE)
                while e2.More():
                    face_rgb.append((e2.Current(), rgb)); e2.Next()
    bb = Bnd_Box(); BRepBndLib.Add_s(shape, bb)
    if bb.IsVoid():
        ex.Next(); continue
    _a, _b = bb.CornerMin(), bb.CornerMax()
    xmn, ymn, zmn, xmx, ymx, zmx = _a.X(), _a.Y(), _a.Z(), _b.X(), _b.Y(), _b.Z()
    if abs((zmx - zmn) - 1.6) < 0.05 and (xmx - xmn) > 30 and board_bounds is None:
        board_bounds = (xmn, ymn, zmn, xmx, ymx, zmx)
        mesh_faces(shape, [], (0.06, 0.26, 0.14))
    else:
        mesh_faces(shape, face_rgb, default)
    ex.Next()
print('faces:', len(meshes), 'board bounds:', [round(v, 2) for v in board_bounds])

# ---------------------------------------------------------------- render
def quad(z):
    x0, y0, _, x1, y1, _ = board_bounds
    pts = np.array([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]])
    q = pv.PolyData(pts, np.array([4, 0, 1, 2, 3]))
    q.active_texture_coordinates = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    return q

def render(view, path, size=(2000, 1700)):
    p = pv.Plotter(off_screen=True, window_size=size, lighting='three lights')
    p.set_background('#161a1f', top='#39434e')
    for pts, faces, col in meshes:
        p.add_mesh(pv.PolyData(pts, faces), color=col, specular=0.35, specular_power=25, ambient=0.18, diffuse=0.85)
    zt, zb = board_bounds[5], board_bounds[2]
    p.add_mesh(quad(zt + 0.012), texture=pv.read_texture(tex['top']), ambient=0.3, diffuse=0.75, specular=0.1)
    p.add_mesh(quad(zb - 0.012), texture=pv.read_texture(tex['bottom']), ambient=0.3, diffuse=0.75, specular=0.1)
    p.enable_anti_aliasing('ssaa')
    x0, y0, _, x1, y1, _ = board_bounds
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2 + 3.0, zt])
    span = max(x1 - x0, y1 - y0 + 6)
    if view in ('top', 'bottom'):
        z = c[2] + span * 4 if view == 'top' else zb - span * 4
        p.camera_position = [(c[0], c[1], z), tuple(c), (0, 1, 0)]
        p.enable_parallel_projection(); p.camera.parallel_scale = span * 0.56
    else:
        d = span * 2.0
        p.camera_position = [(c[0] - d * 0.45, c[1] - d * 0.85, c[2] + d * 0.95), tuple(c), (0, 0, 1)]
        p.camera.view_angle = 28
    p.screenshot(path); p.close()
    print('wrote', path)

for v in views:
    render(v, f'{out}-{v}.png')
