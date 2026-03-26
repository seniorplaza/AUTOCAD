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
    'TRAMEX':     -2420.0,
}
_VAR_COL_X = {40: 3715.34, 50: 4125.46, 60: 4536.58, 80: 4936.11, 100: 5356.11}


def _perfil_seccion(doc, L, g_carril, base, hbase=137):
    """Extrae vértices (lx,ly) del perfil correcto del bloque VARIACIONES."""
    bu = (base or '').upper().replace('Ó','O').replace('É','E').replace('Í','I')
    if 'HORMIGON' in bu:
        return None
    if   'SANEAMIENTO' in bu: rk = 'SANEAMIENTO'
    elif 'TRAMEX'      in bu: rk = 'TRAMEX'
    elif hbase <= 137:         rk = 'L<=6000'
    elif hbase <= 160:         rk = 'L<=7000'
    elif hbase <= 190:         rk = 'L<=8500'
    else:                      rk = 'L>8500'
    y_cell = _VAR_ROW_Y[rk]
    x_cell = _VAR_COL_X.get(g_carril, _VAR_COL_X[40])
    blk = doc.blocks.get("VARIACIONES SECCIÓN_LARGUERO_BASE")
    if not blk:
        print(f"  [WARN] Bloque no encontrado. Nombres con 'VAR': {[b.name for b in doc.blocks if 'VAR' in b.name.upper()]}")
        return None
    all_types = {}
    pl_cer = []
    for e in blk:
        all_types[e.dxftype()] = all_types.get(e.dxftype(), 0) + 1
        if e.dxftype() != 'LWPOLYLINE':
            continue
        layer = e.dxf.layer
        pts = list(e.get_points(format='xyseb'))
        if len(pts) < 4:
            continue
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        if layer == 'PL-CER-DIB':
            pl_cer.append((round(cx,1), round(cy,1)))
        if layer == 'PL-CER-DIB' and (x_cell - 10 < cx < x_cell + 220) and (y_cell - 10 < cy < y_cell + 220):
            return [(p[0] - x_cell, p[1] - y_cell) for p in pts], x_cell, y_cell
    print(f"  [WARN] Perfil no hallado. x_cell={x_cell:.1f} y_cell={y_cell:.1f} rk={rk} g_carril={g_carril} L={L}")
    print(f"  [INFO] Tipos en bloque: {all_types}")
    print(f"  [INFO] PL-CER-DIB centroides ({len(pl_cer)}): {pl_cer[:10]}")
    # Mostrar todas las capas de LWPOLYLINEs del bloque
    capas = set(e.dxf.layer for e in blk if e.dxftype() == 'LWPOLYLINE')
    print(f"  [INFO] Capas LWPOLYLINE en bloque: {capas}")
    return None


def dibujar_seccion_ancho(msp, doc, x0, y0, x1, y1, hbase, g_carril, tipo_tablero, L, base, skip_faces=None):
    """
    Sección del módulo por el lado ancho (A), a la derecha del módulo:
    - Perfil inferior (y0) y superior (y1): desde VARIACIONES con rot. 90°CW+180°
    - Tablero (color 2 amarillo): 18mm fenólico / 19mm hidrófugo
    - Correa (color 4 cian, siempre 99mm de alto)
    - BLOQUE TABLERO SECCIÓN con atributos dinámicos
    """
    if not isinstance(hbase, int):
        return  # HORMIGONADA: pendiente

    _tt = (tipo_tablero or '').upper().replace('Ó','O').replace('É','E').replace('Í','I')
    es_fen   = 'FENOL' in _tt
    es_fibro = 'FIBRO' in _tt
    if es_fibro:
        grosor_t = 8;   tipo_txt = 'TABLERO';   tab_txt = 'FIBROCEMENTO'
    elif es_fen:
        grosor_t = 18;  tipo_txt = 'TABLERO';   tab_txt = 'FENÓLICO'
    else:
        grosor_t = 19;  tipo_txt = 'AGLOMERADO'; tab_txt = 'HIDRÓFUGO'
    A        = float(y1 - y0)

    DX_PROF   = 289.0
    tab_ofs   = g_carril + 40
    cor_ofs   = tab_ofs + 2
    cor_w     = 100
    profile_w = g_carril + 65
    rect_x    = x1 + DX_PROF - (0.1322 if es_fibro else 0.0)
    _skip     = skip_faces or set()
    # CERRADO (no en skip) → tablero tapa el carril → extender 85mm hacia ese lado
    tab_bot = tab_ofs - (85 if 'S' not in _skip else 0)
    tab_top = tab_ofs - (85 if 'N' not in _skip else 0)

    def _poly(pts_xy, layer, color=256):
        msp.add_lwpolyline(pts_xy, close=True, dxfattribs={'layer': layer, 'color': color})

    # Tablero (amarillo) — borde derecho fijo, crece hacia la izquierda
    _poly([(rect_x-grosor_t, y0+tab_bot),
           (rect_x,          y0+tab_bot),
           (rect_x,          y1-tab_top),
           (rect_x-grosor_t, y1-tab_top)], 'Cotas', 2)

    # Correa (cian)
    _poly([(rect_x+2,         y0+cor_ofs),
           (rect_x+2+cor_w,   y0+cor_ofs),
           (rect_x+2+cor_w,   y1-cor_ofs),
           (rect_x+2,         y1-cor_ofs)], 'CORREAS', 4)

    # Perfiles desde VARIACIONES (rot. 90°CW + 180°)
    result = _perfil_seccion(doc, L, g_carril, base, hbase)
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


def dibujar_seccion_abajo(msp, doc, x0, y0, x1, y1, hbase, g_carril, tipo_tablero, L, base, skip_faces=None):
    """
    Sección del módulo por la CARA CORTA, debajo del módulo (para módulos rotados).
    Equivale a dibujar_seccion_ancho rotada 90°: los perfiles van en los extremos X.
    """
    if not isinstance(hbase, int):
        return

    _tt = (tipo_tablero or '').upper().replace('Ó','O').replace('É','E').replace('Í','I')
    es_fen   = 'FENOL' in _tt
    es_fibro = 'FIBRO' in _tt
    if es_fibro:
        grosor_t = 8;   tipo_txt = 'TABLERO';   tab_txt = 'FIBROCEMENTO'
    elif es_fen:
        grosor_t = 18;  tipo_txt = 'TABLERO';   tab_txt = 'FENÓLICO'
    else:
        grosor_t = 19;  tipo_txt = 'AGLOMERADO'; tab_txt = 'HIDRÓFUGO'

    DY_PROF   = 333.5
    tab_ofs   = g_carril + 40
    cor_ofs   = tab_ofs + 2
    cor_w     = 100
    profile_w = g_carril + 65
    rect_y    = y0 - DY_PROF   # borde superior zona sección (justo debajo del módulo)
    _skip     = skip_faces or set()
    # CERRADO (no en skip) → tablero tapa el carril → extender 85mm hacia ese lado
    tab_lft = tab_ofs - (85 if 'W' not in _skip else 0)
    tab_rgt = tab_ofs - (85 if 'E' not in _skip else 0)

    def _poly(pts_xy, layer, color=256):
        msp.add_lwpolyline(pts_xy, close=True, dxfattribs={'layer': layer, 'color': color})

    # Tablero (amarillo) — franja horizontal
    _poly([(x0+tab_lft, rect_y+0.0028),
           (x1-tab_rgt, rect_y+0.0028),
           (x1-tab_rgt, rect_y+0.0028+grosor_t),
           (x0+tab_lft, rect_y+0.0028+grosor_t)], 'Cotas', 2)

    # Correa (cian) — empieza justo debajo del tablero
    _poly([(x0+cor_ofs, rect_y-grosor_t+17.0028),
           (x1-cor_ofs, rect_y-grosor_t+17.0028),
           (x1-cor_ofs, rect_y-grosor_t+17.0028-cor_w),
           (x0+cor_ofs, rect_y-grosor_t+17.0028-cor_w)], 'CORREAS', 4)

    # Perfiles desde VARIACIONES — izquierdo y derecho
    result = _perfil_seccion(doc, L, g_carril, base, hbase)
    if result:
        verts, x_cl, y_cl = result
        lft = [(x0+(profile_w-lx), rect_y-(hbase-ly)) for lx, ly in verts]
        rgt = [(x1-(profile_w-lx), rect_y-(hbase-ly)) for lx, ly in verts]
        _poly(lft, 'PL-CER-DIB')
        _poly(rgt, 'PL-CER-DIB')

    # BLOQUE TABLERO SECCIÓN — centrado horizontalmente bajo los perfiles
    cx_sec = (x0 + x1) / 2.0
    ref = msp.add_blockref('BLOQUE TABLERO SECCIÓN',
                           insert=(cx_sec, rect_y - hbase - 80 - 375),
                           dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {
        'TIPO_TABLERO':          tipo_txt,
        'TABLERO':               tab_txt,
        'NÚMERO_GROSOR_TABLERO': str(grosor_t),
    }, doc)
