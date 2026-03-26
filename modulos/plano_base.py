"""
plano_base.py — Plano de estructura base: pilares, carriles, alzado, zona derecha, textos.
"""
from .config import (
    CARRIL_OFS_H_X, CARRIL_OFS_H_Y, CARRIL_OFS_V_X,
    CARRIL_OFS_V_Y_MAP, CARRIL_OFS_H_X_MAP, CARRIL_OFS_V_Y_MINI,
)

# Largo del tablero en dirección A (ancho del módulo)
TABLERO_LARGO = {'Hidrófugo': 2440, 'Fenólico': 2500, 'Fibrocemento': 2600}
from .dxf_utils import cota_v, cota_h

# ─── OFFSETS ALZADO BASE (relativos a y1 del módulo) ──────────────────────────
_ALZ_RECT_OFS_BOT   = 1186.0   # y1 → borde inferior rect ALZ-EST-BA-DIB
_ALZ_CER_INSERT_OFS = 1318.28  # y1 → insert_y del bloque CORREA BASE
_COTA_HBASE_DX      = -218.0   # desde x0 → cota vertical hbase

# ─── OFFSETS TABLERO INTERIOR (relativos a cx y y0/y1) ────────────────────────
_TAB_DX_SEMI = 480.0
_TAB_DY_TOP  = -843.7
_TAB_DY_BOT  = -1118.2
_TAB_R       = 50.0
_TAB_TXT_DX  = 1365.0   # desde x1
_TAB_TXT_DY  = -1454.0  # desde y1


# ─── PILARES ──────────────────────────────────────────────────────────────────

def insertar_pilares(msp, x0, y0, x1, y1, nombre_bloque):
    if nombre_bloque == 'PILAR PANEL 40 ANCHO 1190':
        esquinas = [(x0,y0,0,-1),(x1,y0,0,1),(x0,y1,180,1),(x1,y1,180,-1)]
    else:
        esquinas = [(x0,y0,180,1),(x1,y0,180,-1),(x0,y1,0,-1),(x1,y1,0,1)]
    for ix, iy, rot, xs in esquinas:
        msp.add_blockref(nombre_bloque, insert=(ix,iy), dxfattribs={
            'layer':'PL-PILARES','rotation':rot,'xscale':xs,'yscale':1})


# ─── CARRILES ─────────────────────────────────────────────────────────────────

def dibujar_carriles(msp, x0, y0, x1, y1, grosor, ancho_modulo=2350, skip_faces=None):
    """2 carriles horizontales + 2 verticales en capa CARRIL (gris).
    skip_faces: conjunto {'N','S','E','W'} — omite los carriles de esas caras (paredes ABIERTO).
    """
    skip = skip_faces or set()
    A = ancho_modulo
    ofs_h_x = CARRIL_OFS_H_X_MAP.get(A, CARRIL_OFS_H_X)
    cx_ini  = x0 + ofs_h_x
    cx_fin  = x1 - ofs_h_x
    for face, cy_base in [('S', y0 + CARRIL_OFS_H_Y), ('N', y1 - CARRIL_OFS_H_Y - grosor)]:
        if face in skip: continue
        msp.add_lwpolyline(
            [(cx_ini, cy_base),(cx_fin, cy_base),(cx_fin, cy_base+grosor),(cx_ini, cy_base+grosor)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})
    ofs_v_y = CARRIL_OFS_V_Y_MINI if A <= 1190 else CARRIL_OFS_V_Y_MAP.get(A, 170)
    cy_ini  = y0 + ofs_v_y
    cy_fin  = y1 - ofs_v_y
    for face, cx_base in [('W', x0 + CARRIL_OFS_V_X), ('E', x1 - CARRIL_OFS_V_X - grosor)]:
        if face in skip: continue
        msp.add_lwpolyline(
            [(cx_base, cy_ini),(cx_base+grosor, cy_ini),(cx_base+grosor, cy_fin),(cx_base, cy_fin)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})
    print(f"  Carriles: grosor={grosor}mm  ofs_h_x={ofs_h_x}  ofs_v_y={ofs_v_y}  skip={skip or '-'}")


# ─── MUÑONES / PILARES (texto) ────────────────────────────────────────────────

def _munon_pilar_str(A, long_pilar, panel_grosor=0):
    """Devuelve (texto_munon, texto_pilar) con dimensiones según ancho y panel."""
    try:
        p = int(panel_grosor) if panel_grosor else 0
    except (ValueError, TypeError):
        p = 0
    if   A <= 1190:  px, py = 125, 125
    elif p > 90:     px, py = 245, 217
    elif A <= 2350:  px, py = 195, 167
    elif A == 2400:  px, py = 220, 167
    elif A == 2440:  px, py = 240, 167
    else:            px, py = 220, 167
    mx, my = px - 20, py - 20
    return (f"MUÑONES {mx}x{my}mm.", f"PILARES {px}x{py}x{long_pilar}mm")


# ─── ALZADO BASE ──────────────────────────────────────────────────────────────

def dibujar_alzado_base(msp, doc, x0, y0, x1, y1, hbase, correas, tipo_tablero, long_pilar, A, g_carril,
                        draw_hbase_cota=True):
    """
    Dibuja encima del módulo:
    - Rectángulo verde ALZ-EST-BA-DIB (largo × hbase)
    - Bloques CORREA BASE en alzado (uno por correa)
    - Cota vertical hbase (PMP-T-75) a la izquierda (omitida si draw_hbase_cota=False)
    """
    alz_y0 = y1 + _ALZ_RECT_OFS_BOT
    alz_y1 = alz_y0 + hbase
    for p1, p2 in [
        ((x0, alz_y0),(x0, alz_y1)),
        ((x0, alz_y1),(x1, alz_y1)),
        ((x1, alz_y1),(x1, alz_y0)),
        ((x1, alz_y0),(x0, alz_y0)),
    ]:
        msp.add_line(p1, p2, dxfattribs={'layer': 'ALZ-EST-BA-DIB'})

    alz_cer_insert_y = y1 + _ALZ_CER_INSERT_OFS
    for pos in correas:
        msp.add_blockref('CORREA BASE',
                         insert=(x0 + pos, alz_cer_insert_y),
                         dxfattribs={'layer': 'ALZ-CER-DIB'})

    if draw_hbase_cota:
        cota_v(msp, doc, x0, alz_y0, x0, alz_y1, x0 + _COTA_HBASE_DX, 'PMP-T-75', color=5)


def dibujar_alzado_base_v(msp, doc, x0, y0, x1, y1, hbase, correas, draw_hbase_cota=True):
    """
    Alzado BASE para módulos ROTADOS: dibuja a la IZQUIERDA del módulo, verticalmente.
    - Rectángulo verde ALZ-EST-BA-DIB (hbase × alto módulo)
    - Bloques CORREA BASE (rotados 270°) en las posiciones Y de las correas
    - Cota horizontal hbase (PMP-T-75) sobre el rectángulo
    """
    alz_x1 = x0 - _ALZ_RECT_OFS_BOT        # borde derecho rect (pegado al módulo)
    alz_x0 = alz_x1 - hbase                 # borde izquierdo
    for p1, p2 in [
        ((alz_x0, y0), (alz_x0, y1)),
        ((alz_x0, y1), (alz_x1, y1)),
        ((alz_x1, y1), (alz_x1, y0)),
        ((alz_x1, y0), (alz_x0, y0)),
    ]:
        msp.add_line(p1, p2, dxfattribs={'layer': 'ALZ-EST-BA-DIB'})

    # Insert en el borde izquierdo (exterior) del rect; rotation=90 extiende el bloque en +Y (a lo largo del módulo)
    for pos in correas:
        msp.add_blockref('CORREA BASE',
                         insert=(x0 - _ALZ_CER_INSERT_OFS, y0 + pos),
                         dxfattribs={'layer': 'ALZ-CER-DIB', 'rotation': 90})

    if draw_hbase_cota:
        # Cota horizontal sobre el rectángulo (arriba)
        cota_h(msp, doc, alz_x0, y1, alz_x1, y1, y1 - _COTA_HBASE_DX, 'PMP-T-75', color=5)


# ─── ZONA DERECHA (sección carril) ────────────────────────────────────────────

def dibujar_zona_derecha(msp, x0, y0, x1, y1, g_carril, A):
    """
    Geometría fija a la derecha del módulo: sección del carril vertical,
    detalle panel, círculo y líneas de referencia.
    """
    def _poly(pts, layer, color=256):
        msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': layer, 'color': color})
    def _line(p1, p2, layer, color=256):
        msp.add_line(p1, p2, dxfattribs={'layer': layer, 'color': color})

    dx_cua  = 270;  dx_cua2 = 289
    dx_cor1 = 291
    dx_cor2 = dx_cor1 + g_carril + 62
    dx_plc1 = 289;  dx_plc2 = 429

    _poly([(x1+dx_cua,  y0-20),(x1+dx_cua2, y0-20),
           (x1+dx_cua2, y1+20),(x1+dx_cua,  y1+20)], 'CUADROS')

    ofs_y = 82
    _poly([(x1+dx_cor1, y0+ofs_y),(x1+dx_cor2, y0+ofs_y),
           (x1+dx_cor2, y1-ofs_y),(x1+dx_cor1, y1-ofs_y)], 'CORREAS')

    dy_plc_h = 105;  dy_plc_ofs = 84
    for cy_base, sign in [(y1, -1), (y0, +1)]:
        _poly([(x1+dx_plc1, cy_base+sign*0),(x1+dx_plc2, cy_base+sign*0),
               (x1+dx_plc2, cy_base+sign*dy_plc_h),(x1+dx_plc1, cy_base+sign*dy_plc_h)], 'PL-CER-DIB')
        _poly([(x1+dx_plc1+2, cy_base+sign*2),(x1+dx_plc2-2, cy_base+sign*2),
               (x1+dx_plc2-2, cy_base+sign*(dy_plc_h-2)),(x1+dx_plc1+2, cy_base+sign*(dy_plc_h-2))], 'PL-CER-DIB')
        xr = x1+dx_plc2;  xl = x1+dx_plc1+(dx_plc2-dx_plc1)-34
        _line((xr,   cy_base+sign*0),           (xr,   cy_base+sign*dy_plc_ofs),       'PL-CER-DIB')
        _line((xr-2, cy_base+sign*2),           (xr-2, cy_base+sign*(dy_plc_ofs-2)),   'PL-CER-DIB')
        _line((xl,   cy_base+sign*dy_plc_ofs),  (xr,   cy_base+sign*dy_plc_ofs),       'PL-CER-DIB')
        _line((xl-2, cy_base+sign*(dy_plc_ofs-2)),(xr-2,cy_base+sign*(dy_plc_ofs-2)), 'PL-CER-DIB')
        _line((xl,   cy_base+sign*dy_plc_ofs),  (xl,   cy_base+sign*dy_plc_h),         'PL-CER-DIB')
        _line((xl-2, cy_base+sign*(dy_plc_ofs-2)),(xl-2,cy_base+sign*(dy_plc_h-2)),   'PL-CER-DIB')
        _line((xl-2, cy_base+sign*(dy_plc_h-2)),(xl,   cy_base+sign*(dy_plc_h-2)),    'PL-CER-DIB')

    dx_det = 981;  det_w = 210;  det_h = 280;  det_y = y0
    _poly([(x1+dx_det,       det_y-det_h),(x1+dx_det+det_w, det_y-det_h),
           (x1+dx_det+det_w, det_y),(x1+dx_det, det_y)], 'PL-CER-DIB')
    _poly([(x1+dx_det+4,       det_y-4),(x1+dx_det+det_w-4, det_y-4),
           (x1+dx_det+det_w-4, det_y-det_h+4),(x1+dx_det+4, det_y-det_h+4)], 'PL-CER-DIB')
    for p1, p2 in [
        ((x1+dx_det+det_w,    det_y),     (x1+dx_det+det_w-42, det_y)),
        ((x1+dx_det+det_w-4,  det_y-4),   (x1+dx_det+det_w-46, det_y-4)),
        ((x1+dx_det+det_w-42, det_y),     (x1+dx_det+det_w-42, det_y-68)),
        ((x1+dx_det+det_w-46, det_y-4),   (x1+dx_det+det_w-46, det_y-64)),
        ((x1+dx_det,          det_y-68),  (x1+dx_det+det_w-42, det_y-68)),
        ((x1+dx_det,          det_y-64),  (x1+dx_det+det_w-46, det_y-64)),
        ((x1+dx_det,          det_y-68),  (x1+dx_det,          det_y-64)),
        ((x1+dx_det,          det_y-det_h+4),(x1+dx_det,       det_y-det_h)),
    ]:
        _line(p1, p2, 'PL-CER-DIB')

    dx_cor_det = 675;  cor_det_w = 349;  cor_det_h = 204
    cor_det_y1 = det_y - 4;  cor_det_y0 = cor_det_y1 - cor_det_h
    _poly([(x1+dx_cor_det, cor_det_y0),(x1+dx_cor_det+cor_det_w, cor_det_y0),
           (x1+dx_cor_det+cor_det_w, cor_det_y1),(x1+dx_cor_det, cor_det_y1)], 'CORREAS')

    cu_w = 372;  cu_h = 33;  cu_y = cor_det_y0
    _poly([(x1+658, cu_y-cu_h),(x1+658+cu_w, cu_y-cu_h),
           (x1+658+cu_w, cu_y),(x1+658, cu_y)], 'CUADROS')

    msp.add_circle((x1+371, y0+59), radius=130, dxfattribs={'layer': 'Cotas'})
    _line((x1+289, y1-105), (x1+291, y1-105), 'Cotas')
    _line((x1+632, y0+204), (x1+797, y0+373), 'Cotas')
    _line((x1+874, y0+326), (x1+965, y0+568), 'Cotas')


# ─── FLEJE FIBROCEMENTO ───────────────────────────────────────────────────────

def dibujar_fleje(msp, doc, x0, y0, x1, y1, g_carril, tipo_tablero, x_cota):
    """
    Dibuja el fleje horizontal cuando A > largo del tablero.
    Aplica a los 3 tipos: Hidrófugo (2440), Fenólico (2500), Fibrocemento (2600).
    El tablero principal arranca desde arriba (y1); el fleje apoya su extremo inferior.
    Posición: fleje_y = y1 - CARRIL_OFS_H_Y - g_carril - largo_tablero
    Geometría:
      1. LWPOLYLINE roja (color=1), const_width=100 → banda visible del fleje
      2. LWPOLYLINE trazo-y-punto (TRAZOS2), color=1 → línea de eje centrada
      3. Dos cota_v en x_cota: pieza inferior y tablero superior con tipo como sufijo
    """
    largo = TABLERO_LARGO.get(tipo_tablero, 2440)
    fleje_y = y1 - CARRIL_OFS_H_Y - g_carril - largo
    # Banda roja
    _pl = msp.add_lwpolyline(
        [(x0, fleje_y), (x1, fleje_y)],
        dxfattribs={'layer': 'CORREAS', 'color': 1})
    _pl.dxf.const_width = 100
    # Línea de eje trazo-y-punto color RGB(189,142,0)
    _dash = msp.add_lwpolyline(
        [(x0, fleje_y), (x1, fleje_y)],
        dxfattribs={'layer': 'CORREAS', 'linetype': 'TRAZOS2', 'ltscale': 10})
    _dash.dxf.true_color = (189 << 16) | (142 << 8) | 0  # = 12422656
    # Bordes interiores de los carriles horizontales
    y_car_bot = y0 + CARRIL_OFS_H_Y + g_carril
    y_car_top = y1 - CARRIL_OFS_H_Y - g_carril
    # Cota tablero superior (fleje → carril_top) con tipo de tablero como sufijo
    cota_v(msp, doc, x0, fleje_y,   x0, y_car_top, x_cota, 'PMP-T-60', suffix=tipo_tablero)
    # Cota pieza inferior (carril_bot → fleje) sin sufijo
    cota_v(msp, doc, x0, y_car_bot, x0, fleje_y,   x_cota, 'PMP-T-60')
    pieza_inf = fleje_y - y_car_bot
    print(f"  Fleje {tipo_tablero}: y={fleje_y:.1f}  tablero={largo}mm  pieza_inf={pieza_inf:.0f}mm")


# ─── TEXTOS DENTRO DEL MÓDULO ─────────────────────────────────────────────────

def dibujar_textos_modulo(msp, x0, y0, x1, y1, base, acabado, serie):
    """
    Textos centrados dentro del módulo (tipo+acabado, serie) y texto tablero a la derecha.
    """
    cx = (x0 + x1) / 2.0
    _b = (base or '').strip().upper()
    es_fenolico = 'FENOL' in _b.replace('Ó','O').replace('É','E').replace('Í','I')
    tipo_txt  = 'Fenólico' if es_fenolico else 'Hidrófugo'
    grosor_t  = 18 if es_fenolico else 19

    linea1 = f'{tipo_txt.upper()} + {(acabado or "").strip().upper()}'
    msp.add_mtext(linea1, dxfattribs={
        'layer': 'TEXTO', 'char_height': 112.5,
        'insert': (cx, y0 + 994), 'attachment_point': 5})

    if serie:
        msp.add_mtext(serie.strip().replace(',', ' - '), dxfattribs={
            'layer': 'TEXTO', 'char_height': 112.5,
            'insert': (cx, y0 + 1369), 'attachment_point': 5})

    txt_tab = f'Aglomerado\\P{tipo_txt} {grosor_t}mm'
    msp.add_mtext(txt_tab, dxfattribs={
        'layer': 'TEXTO', 'char_height': 75.0, 'width': 927.0,
        'insert': (x1 + _TAB_TXT_DX, y1 + _TAB_TXT_DY), 'attachment_point': 5})
