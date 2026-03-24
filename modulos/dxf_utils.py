"""
dxf_utils.py — Utilidades DXF: cotas, atributos de bloques, polilíneas redondeadas, hatch.
"""
import math
from .config import DIMSTYLE


# ─── COTAS ────────────────────────────────────────────────────────────────────

def cota_h(msp, doc, xa, ya, xb, yb, dim_y, dimstyle=DIMSTYLE, suffix=''):
    dim = msp.add_linear_dim(
        base=(xa, dim_y), p1=(xa, ya), p2=(xb, yb),
        angle=0, dimstyle=dimstyle, dxfattribs={'layer':'Cotas'})
    if suffix:
        dim.set_text(f'<> {suffix}')
    dim.render()


def cota_v(msp, doc, xa, ya, xb, yb, dim_x, dimstyle=DIMSTYLE):
    dim = msp.add_linear_dim(
        base=(dim_x, ya), p1=(xa, ya), p2=(xb, yb),
        angle=90, dimstyle=dimstyle, dxfattribs={'layer':'Cotas'})
    dim.render()


# ─── ATRIBUTOS DE BLOQUE ──────────────────────────────────────────────────────

def _attribs(blk_ref, vals, doc=None):
    """
    Rellena los ATTRIBs de un INSERT con el dict {tag: valor}.
    Solo aplica align_point cuando halign requiere dos puntos (3=ALIGNED, 4=MIDDLE, 5=FIT).
    """
    try:
        blk_ref.add_auto_attribs(vals)
        blk_ref.attribs_follow = True
        for _a in blk_ref.attribs:
            _a.dxf.valign = 0
        if doc is not None:
            blk_name = blk_ref.dxf.name
            blk_def  = doc.blocks.get(blk_name)
            if blk_def:
                attdef_map = {e.dxf.tag: e for e in blk_def if e.dxftype() == 'ATTDEF'}
                ix, iy = blk_ref.dxf.insert.x, blk_ref.dxf.insert.y
                for attrib in blk_ref.attribs:
                    tag = attrib.dxf.tag
                    if tag not in attdef_map:
                        continue
                    attdef = attdef_map[tag]
                    halign = getattr(attdef.dxf, 'halign', 0)
                    if halign in (3, 4, 5):
                        try:
                            ap = attdef.dxf.align_point
                            attrib.dxf.align_point = (ix + ap.x, iy + ap.y)
                        except Exception:
                            pass
                    else:
                        try:
                            del attrib.dxf.align_point
                        except Exception:
                            pass
    except Exception:
        pass


# ─── FORMAS GEOMÉTRICAS ───────────────────────────────────────────────────────

def _rect_redondeado(msp, x_ini, y_bot, x_fin, y_top, radio, layer, color):
    """Rectángulo con esquinas redondeadas (LWPOLYLINE con bulge, 90° por esquina)."""
    b = 0.414  # tan(22.5°) ≈ cuarto de círculo
    r = radio
    pts = [
        (x_ini + r, y_top,   -b),
        (x_fin - r, y_top,  0.0),
        (x_fin,     y_top - r, -b),
        (x_fin,     y_bot + r, 0.0),
        (x_fin - r, y_bot,   -b),
        (x_ini + r, y_bot,  0.0),
        (x_ini,     y_bot + r, -b),
        (x_ini,     y_top - r, 0.0),
    ]
    msp.add_lwpolyline(
        [(p[0], p[1], 0, 0, p[2]) for p in pts],
        format='xyseb', close=True,
        dxfattribs={'layer': layer, 'color': color})


def _hatch_rect_redondeado(msp, cx, dy_top, dy_bot, semiancho, radio, color_hatch, layer_hatch):
    """HATCH sólido en un rect redondeado mediante EdgePath."""
    hatch = msp.add_hatch(dxfattribs={'layer': layer_hatch, 'color': color_hatch})
    hatch.set_solid_fill(color=color_hatch)
    ep = hatch.paths.add_edge_path()
    x0h = cx - semiancho
    x1h = cx + semiancho
    r   = radio
    yb  = dy_bot
    yt  = dy_top
    ep.add_arc(center=(x0h + r, yt - r), radius=r, start_angle=90,  end_angle=180, ccw=True)
    ep.add_line(start=(x0h, yt - r),     end=(x0h, yb + r))
    ep.add_arc(center=(x0h + r, yb + r), radius=r, start_angle=180, end_angle=270, ccw=True)
    ep.add_line(start=(x0h + r, yb),     end=(x1h - r, yb))
    ep.add_arc(center=(x1h - r, yb + r), radius=r, start_angle=270, end_angle=360, ccw=True)
    ep.add_line(start=(x1h, yb + r),     end=(x1h, yt - r))
    ep.add_arc(center=(x1h - r, yt - r), radius=r, start_angle=0,   end_angle=90,  ccw=True)
    ep.add_line(start=(x1h - r, yt),     end=(x0h + r, yt))
