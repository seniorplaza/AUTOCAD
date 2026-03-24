"""
seccion_ancho.py — Sección del lado ancho del módulo (plano de estructura base, zona derecha).
Extrae el perfil de VARIACIONES SECCIÓN_LARGUERO_BASE y lo dibuja en sección con tablero y correa.
"""
from .dxf_utils import _attribs

# ─── GRID DE VARIACIONES SECCIÓN_LARGUERO_BASE ────────────────────────────────
# Filas → rango de L;  Columnas → grosor de carril
_VAR_ROW_Y = {
    'L<=6000':    2180.25,
    'L<=7000':    1253.25,
    'L<=8500':     327.25,
    'L>8500':     -640.25,
    'SANEAMIENTO':-1647.25,
}
_VAR_COL_X = {40: 3715.34, 50: 4125.46, 60: 4536.58, 80: 4936.11, 100: 5356.11}


def _perfil_seccion(doc, L, g_carril, base):
    """Extrae vértices (lx,ly) del perfil correcto del bloque VARIACIONES."""
    bu = (base or '').upper().replace('Ó','O').replace('É','E').replace('Í','I')
    if 'HORMIGON' in bu:
        return None
    if   'SANEAMIENTO' in bu: rk = 'SANEAMIENTO'
    elif L <= 6000:            rk = 'L<=6000'
    elif L <= 7000:            rk = 'L<=7000'
    elif L <= 8500:            rk = 'L<=8500'
    else:                      rk = 'L>8500'
    y_cell = _VAR_ROW_Y[rk]
    x_cell = _VAR_COL_X.get(g_carril, _VAR_COL_X[40])
    blk = doc.blocks.get("VARIACIONES SECCIÓN_LARGUERO_BASE")
    if not blk:
        return None
    for e in blk:
        if e.dxftype() != 'LWPOLYLINE' or e.dxf.layer != 'PL-CER-DIB':
            continue
        pts = list(e.get_points(format='xyseb'))
        if len(pts) < 4:
            continue
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        if (x_cell - 10 < cx < x_cell + 220) and (y_cell - 10 < cy < y_cell + 220):
            return [(p[0] - x_cell, p[1] - y_cell) for p in pts], x_cell, y_cell
    return None


def dibujar_seccion_ancho(msp, doc, x0, y0, x1, y1, hbase, g_carril, tipo_tablero, L, base):
    """
    Sección del módulo por el lado ancho (A), a la derecha del módulo:
    - Perfil inferior (y0) y superior (y1): desde VARIACIONES con rot. 90°CW+180°
    - Tablero (color 2 amarillo): 18mm fenólico / 19mm hidrófugo
    - Correa (color 4 cian, siempre 99mm de alto)
    - BLOQUE TABLERO SECCIÓN con atributos dinámicos
    """
    if not isinstance(hbase, int):
        return  # HORMIGONADA: pendiente

    es_fen   = 'FENOL' in (tipo_tablero or '').upper().replace('Ó','O').replace('É','E').replace('Í','I')
    grosor_t = 18 if es_fen else 19
    tipo_txt = 'TABLERO'   if es_fen else 'AGLOMERADO'
    tab_txt  = 'FENÓLICO'  if es_fen else 'HIDRÓFUGO'
    A        = float(y1 - y0)

    DX_TAB    = 270.0
    DX_PROF   = DX_TAB + grosor_t
    tab_ofs   = g_carril + 40
    cor_ofs   = tab_ofs + 2
    cor_w     = 99
    profile_w = g_carril + 65

    def _poly(pts_xy, layer, color=256):
        msp.add_lwpolyline(pts_xy, close=True, dxfattribs={'layer': layer, 'color': color})

    # Tablero (amarillo)
    _poly([(x1+DX_TAB,            y0+tab_ofs),
           (x1+DX_TAB+grosor_t,   y0+tab_ofs),
           (x1+DX_TAB+grosor_t,   y1-tab_ofs),
           (x1+DX_TAB,            y1-tab_ofs)], 'Cotas', 2)

    # Correa (cian)
    _poly([(x1+DX_PROF+2,         y0+cor_ofs),
           (x1+DX_PROF+2+cor_w,   y0+cor_ofs),
           (x1+DX_PROF+2+cor_w,   y1-cor_ofs),
           (x1+DX_PROF+2,         y1-cor_ofs)], 'CORREAS', 4)

    # Perfiles desde VARIACIONES (rot. 90°CW + 180°)
    result = _perfil_seccion(doc, L, g_carril, base)
    if result:
        verts, x_cl, y_cl = result
        bot = [(x1+DX_PROF+(hbase-ly), y0+(profile_w-lx)) for lx, ly in verts]
        top = [(x1+DX_PROF+(hbase-ly), y1-(profile_w-lx)) for lx, ly in verts]
        _poly(bot, 'PL-CER-DIB')
        _poly(top, 'PL-CER-DIB')

    # BLOQUE TABLERO SECCIÓN
    ref = msp.add_blockref('BLOQUE TABLERO SECCIÓN',
                           insert=(x1+DX_PROF+hbase+30, y0+A/2-139),
                           dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {
        'TIPO_TABLERO':          tipo_txt,
        'TABLERO':               tab_txt,
        'NÚMERO_GROSOR_TABLERO': str(grosor_t),
    }, doc)
