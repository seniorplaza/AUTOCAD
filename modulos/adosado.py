"""
adosado.py — Generación de DXF para conjuntos de módulos adosados.
Orquesta el dibujo de múltiples módulos según el layout del configurador.
"""
import json as _json
import datetime
import ezdxf
from ezdxf.enums import TextEntityAlignment

from .config       import COL, CARRIL_OFS_V_X, CARRIL_OFS_H_Y
from .calculos     import calc_hbase, nombre_bloque_pilar, grosor_carril, calc_correas, hex_a_ral
from .limpiar      import limpiar_modulo
from .dxf_utils    import cota_h, cota_v, _attribs
from .plano_base   import (insertar_pilares, dibujar_carriles,
                           dibujar_alzado_base, dibujar_fleje, TABLERO_LARGO)
from .seccion_ancho import dibujar_seccion_ancho
from .bloques      import dibujar_bloques_recuadros


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cf(fila, col):
    idx = COL.get(col, -1)
    return fila[idx].strip() if 0 <= idx < len(fila) else ""


def _parse_series(serie_str):
    """'36888-36890' → ['36888','36889','36890']  |  '36888-36889-36890' → lista directa."""
    if not serie_str:
        return []
    partes = [p.strip() for p in serie_str.replace(' ', '').split('-') if p.strip()]
    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
        start, end = int(partes[0]), int(partes[1])
        return [str(n) for n in range(start, end + 1)]
    return partes


def _tipo_tablero(base):
    b = (base or '').strip().upper().replace('Ó','O').replace('É','E').replace('Í','I')
    if 'FIBRO' in b:  return 'Fibrocemento'
    if 'FENOL' in b:  return 'Fenólico'
    return 'Hidrófugo'


def _setup_dimstyles(doc):
    """Crea PMP-T-50 y PMP-T-60 si no existen (igual que en generar_modulo)."""
    ATTRS = ['dimtxt','dimasz','dimexo','dimexe','dimdli','dimdle',
             'dimtad','dimtih','dimtoh','dimgap','dimblk','dimblk1','dimblk2','dimsah','dimdec']
    ds75 = doc.dimstyles.get('PMP-T-75')
    for nombre, escala in [('PMP-T-50', 50.0), ('PMP-T-60', 60.0)]:
        if not doc.dimstyles.has_entry(nombre) and ds75 is not None:
            ds_new = doc.dimstyles.new(nombre)
            ds_new.dxf.dimscale = escala
            for attr in ATTRS:
                try: setattr(ds_new.dxf, attr, getattr(ds75.dxf, attr))
                except: pass
        if doc.dimstyles.has_entry(nombre):
            doc.dimstyles.get(nombre).dxf.dimtxsty = 'ARIAL'
    if ds75:
        ds75.dxf.dimtxsty = 'ARIAL'


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────────────

def generar_adosado(filas_conj, adosamiento, ruta_plantilla, ruta_salida):
    """
    Genera un DXF con todos los módulos del conjunto adosado.

    filas_conj  : lista de filas CSV marcadas como CONJ (ordenadas)
    adosamiento : dict {'placed': [{modulo, l, a, x, y, ...}, ...]}
    """
    placed = adosamiento.get('placed', [])
    if not placed:
        print("  [WARN] adosamiento sin módulos placed — omitido")
        return

    # ── Spec lookup: modulo label → fila CSV ──────────────────────────────────
    specs = {}
    for fila in filas_conj:
        mod = _cf(fila, 'modulo') or 'M1'
        if mod not in specs:
            specs[mod] = fila
    fila0 = filas_conj[0]   # fila de referencia para cajetín/bloques

    def c0(col): return _cf(fila0, col)

    # ── Bounding box total (mm) ───────────────────────────────────────────────
    L_total = max(p['x'] + p['l'] for p in placed)
    A_total = max(p['y'] + p['a'] for p in placed)

    print(f"  Adosado: {len(placed)} módulos  BBox={L_total}×{A_total}mm")

    # ── Cargar plantilla ──────────────────────────────────────────────────────
    doc = ezdxf.readfile(ruta_plantilla)
    msp = doc.modelspace()
    try: doc.layers.get("CARRIL").dxf.color  = 8
    except: pass
    try: doc.layers.get("CORREAS").dxf.color = 4
    except: pass
    _setup_dimstyles(doc)
    limpiar_modulo(msp)

    # ── Marco A3 dinámico (igual lógica que generar_modulo) ───────────────────
    MARCO_BASE_X0   = 393890.0
    MARCO_BASE_Y0   = -111189.4
    RATIO_A3        = 7110.0 / 5028.0
    MARGEN_X        = 1550.0
    MARGEN_Y_SUP    = 450.0
    OFS_COR_BOT     = 321.0
    _ESPACIO_ENCIMA = 3009.6 + MARGEN_Y_SUP
    A3_W, A3_H      = 7110.0, 5028.0

    contenido_h = OFS_COR_BOT + float(A_total) + _ESPACIO_ENCIMA
    h_min = max(contenido_h + 2 * OFS_COR_BOT, A3_H)
    w_min = max(float(L_total) + 2 * MARGEN_X, A3_W)
    if w_min / h_min > RATIO_A3:
        marco_w = w_min;  marco_h = marco_w / RATIO_A3
    else:
        marco_h = h_min;  marco_w = marco_h * RATIO_A3

    total_real   = OFS_COR_BOT + float(A_total) + 3009.6
    MARGEN_Y_INF = OFS_COR_BOT + (marco_h - total_real) / 2.0

    MARCO_X0 = MARCO_BASE_X0
    MARCO_Y0 = MARCO_BASE_Y0
    MARCO_X1 = MARCO_X0 + marco_w
    MARCO_Y1 = MARCO_Y0 + marco_h

    # ── Cajetín ───────────────────────────────────────────────────────────────
    BLOQUE_W, BLOQUE_H = 7109.9, 5027.7
    sx = marco_w / BLOQUE_W
    sy = marco_h / BLOQUE_H

    _fecha_raw = c0("fecha") or datetime.date.today().strftime("%d/%m/%Y")
    try:
        _d, _m, _y = _fecha_raw.strip().split("/")
        fecha = f"{int(_d):02d}/{int(_m):02d}/{_y}"
    except Exception:
        fecha = _fecha_raw

    col_est = hex_a_ral(c0("colorEstructura"))
    _caj = {
        'OB':         c0("destino") or c0("cliente") or "-",
        'RAL':        col_est or "-",
        'NS':         c0("serie") or "-",
        'SUMINISTRO': c0("suministro") or "ARMADO",
        'FECHA':      fecha,
        'OFERTA':     c0("numPedido") or c0("oferta") or "-",
        'D.P.Y.':     'D.P.Y.',
        'REV-0':      'REV-0',
    }
    blk_def = doc.blocks.get('CAJETIN_VALS')
    for ent in blk_def:
        if ent.dxftype() == 'ATTDEF':
            tag = ent.dxf.tag.upper()
            if tag in _caj:
                ent.dxf.text = str(_caj[tag])

    for ent in list(msp):
        if ent.dxftype() == 'INSERT' and 'CAJET' in ent.dxf.name.upper():
            msp.delete_entity(ent)
            break

    for blk_ent in blk_def:
        t = blk_ent.dxftype()
        if t == 'LWPOLYLINE':
            pts = list(blk_ent.get_points(format='xyseb'))
            new_pts = [(MARCO_X0+p[0]*sx, MARCO_Y0+p[1]*sy, p[2], p[3], p[4]) for p in pts]
            msp.add_lwpolyline(new_pts, format='xyseb', close=True, dxfattribs={
                'layer': blk_ent.dxf.layer, 'color': getattr(blk_ent.dxf,'color',256)})
        elif t == 'MTEXT':
            msp.add_mtext(blk_ent.text, dxfattribs={
                'insert':           (MARCO_X0+blk_ent.dxf.insert.x*sx,
                                     MARCO_Y0+blk_ent.dxf.insert.y*sy, 0),
                'char_height':      blk_ent.dxf.char_height * min(sx,sy),
                'width':            blk_ent.dxf.width * sx,
                'attachment_point': blk_ent.dxf.attachment_point,
                'layer':            blk_ent.dxf.layer,
                'color':            getattr(blk_ent.dxf,'color',256)})
        elif t == 'ATTDEF':
            txt = msp.add_text(blk_ent.dxf.text, dxfattribs={
                'height': blk_ent.dxf.height * min(sx,sy),
                'layer':  blk_ent.dxf.layer,
                'style':  getattr(blk_ent.dxf,'style','Standard'),
                'color':  getattr(blk_ent.dxf,'color',256)})
            txt.set_placement(
                (MARCO_X0+blk_ent.dxf.insert.x*sx,
                 MARCO_Y0+(blk_ent.dxf.insert.y+blk_ent.dxf.height*0.5)*sy),
                align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Coordenadas base del conjunto ─────────────────────────────────────────
    AREA_CX = (MARCO_X0 + MARCO_X1) / 2.0
    x_base  = AREA_CX - float(L_total) / 2.0
    y_base  = MARCO_Y0 + MARGEN_Y_INF

    # Posición total (para cotas globales y bloques)
    x0_tot = x_base
    y0_tot = y_base
    x1_tot = x_base + L_total
    y1_tot = y_base + A_total

    # Offsets de cotas
    OFS_COR_BOT_I = 321;  OFS_TOT = 587;  OFS_TAB = 270;  OFS_IZQ = 321

    # ── Detección de bordes (en coordenadas mm del layout) ────────────────────
    EPS        = 5
    y0_min_mm  = min(p['y']           for p in placed)
    y1_max_mm  = max(p['y'] + p['a']  for p in placed)
    x1_max_mm  = max(p['x'] + p['l']  for p in placed)   # = L_total

    # ── Series por módulo (modulo_label → lista de nº serie) ─────────────────
    serie_nums = {}
    for fila in filas_conj:
        mod = _cf(fila, 'modulo') or 'M1'
        if mod not in serie_nums:
            serie_nums[mod] = _parse_series(_cf(fila, 'serie'))

    # ── Dibujar cada módulo ───────────────────────────────────────────────────
    modulos_info = []   # guardamos info por módulo para cotas totales

    for p in placed:
        fila_m   = specs.get(p['modulo'], fila0)
        L_m  = p['l'];  A_m = p['a']
        x0_m = x_base + p['x']
        y0_m = y_base + p['y']
        x1_m = x0_m + L_m
        y1_m = y0_m + A_m

        # ¿Está este módulo en el borde superior / inferior / derecho?
        is_top    = abs((p['y'] + p['a']) - y1_max_mm) < EPS
        is_bottom = abs(p['y']            - y0_min_mm) < EPS
        is_right  = abs((p['x'] + p['l']) - x1_max_mm) < EPS

        base_m   = _cf(fila_m, 'base')
        panel_m  = _cf(fila_m, 'panelGrosor')
        tipo_m   = _tipo_tablero(base_m)
        hbase_m  = calc_hbase(L_m, A_m, base_m, panel_m)
        hbase_d  = hbase_m if isinstance(hbase_m, int) else (140 if "140" in str(hbase_m) else 160)
        g_car_m  = grosor_carril(panel_m)
        correas_m, tablero_m = calc_correas(L_m, base_m, A_m, g_car_m)
        blk_pil_m = nombre_bloque_pilar(A_m, panel_m)

        print(f"    {p['modulo']} ({L_m}×{A_m})  pos=({p['x']},{p['y']})  "
              f"hbase={hbase_m}  correas={len(correas_m)}")

        # Contorno
        msp.add_lwpolyline(
            [(x0_m,y0_m),(x1_m,y0_m),(x1_m,y1_m),(x0_m,y1_m)],
            close=True, dxfattribs={'layer':'PL-LIM-CASETA'})

        # Correas
        for pos in correas_m:
            msp.add_line((x0_m+pos,y0_m),(x0_m+pos,y1_m),
                         dxfattribs={'layer':'CORREAS','color':4})

        # Carriles
        dibujar_carriles(msp, x0_m, y0_m, x1_m, y1_m, g_car_m, A_m)

        # Cotas correas (debajo) — solo en el módulo más bajo
        if is_bottom:
            puntos_x = [x0_m] + [x0_m+pos for pos in correas_m] + [x1_m]
            for i in range(len(puntos_x)-1):
                cota_h(msp, doc, puntos_x[i], y0_m, puntos_x[i+1], y0_m,
                       y0_m - OFS_COR_BOT_I, 'PMP-T-50')

        # Cotas tablero y cota L — solo en el módulo más alto
        if is_top:
            if correas_m:
                x_ti = x0_m + CARRIL_OFS_V_X + g_car_m + 5
                x_tf = x1_m - CARRIL_OFS_V_X - g_car_m - 5
                span = x_tf - x_ti
                n_full = int(span // tablero_m)
                if n_full > 0:
                    partial = span - n_full * tablero_m
                    if partial <= tablero_m / 2:
                        if partial < tablero_m / 2:
                            n_full -= 1; partial = span - n_full * tablero_m
                        first = x_ti + partial / 2.0
                        if partial / 2.0 > 1:
                            cota_h(msp, doc, x_ti, y1_m, first, y1_m, y1_m+OFS_TAB, 'PMP-T-50', tipo_m)
                        for i in range(n_full):
                            cota_h(msp, doc, first+i*tablero_m, y1_m, first+(i+1)*tablero_m, y1_m, y1_m+OFS_TAB, 'PMP-T-50', tipo_m)
                        last = first + n_full * tablero_m
                        if x_tf - last > 1:
                            cota_h(msp, doc, last, y1_m, x_tf, y1_m, y1_m+OFS_TAB, 'PMP-T-50', tipo_m)
                    else:
                        x_t = x_ti
                        while x_t < x_tf:
                            fin = min(x_t + tablero_m, x_tf)
                            cota_h(msp, doc, x_t, y1_m, fin, y1_m, y1_m+OFS_TAB, 'PMP-T-50', tipo_m)
                            x_t += tablero_m
                else:
                    cota_h(msp, doc, x_ti, y1_m, x_tf, y1_m, y1_m+OFS_TAB, 'PMP-T-50', tipo_m)
            cota_h(msp, doc, x0_m, y1_m, x1_m, y1_m, y1_m+OFS_TOT, 'PMP-T-60')

        # Cota A (izquierda) — todos los módulos
        hay_fleje_m = (A_m - 2*(CARRIL_OFS_H_Y + g_car_m)) > TABLERO_LARGO.get(tipo_m, 2440)
        ofs_cota_a  = OFS_IZQ + 200 if hay_fleje_m else OFS_IZQ
        cota_v(msp, doc, x0_m, y0_m, x0_m, y1_m, x0_m - ofs_cota_a, 'PMP-T-60')
        if hay_fleje_m:
            dibujar_fleje(msp, doc, x0_m, y0_m, x1_m, y1_m, g_car_m, tipo_m,
                          x_cota=x0_m - OFS_IZQ + 110)

        # Alzado base — solo en el módulo más alto
        if is_top:
            dibujar_alzado_base(msp, doc, x0_m, y0_m, x1_m, y1_m,
                                hbase_d, correas_m, tipo_m, int(_cf(fila_m,'h') or 2500)+25, A_m, g_car_m)

        # Sección ancho — solo módulos en el borde derecho
        if is_right:
            dibujar_seccion_ancho(msp, doc, x0_m, y0_m, x1_m, y1_m,
                                  hbase_d, g_car_m, tipo_m, L_m, base_m)

        # Nº serie individual por módulo — solo si el conjunto tiene más de 1 módulo
        if len(placed) > 1:
            pool_idx  = int(p.get('poolId', '_0').split('_')[-1])
            nums_mod  = serie_nums.get(p['modulo'], [])
            serie_val = nums_mod[pool_idx] if pool_idx < len(nums_mod) else (nums_mod[0] if nums_mod else '-')
            cx_m = (x0_m + x1_m) / 2.0
            cy_m = (y0_m + y1_m) / 2.0
            ref_serie = msp.add_blockref('Nº_SERIE_MÓDULO_CONJUNTO',
                                         insert=(cx_m, cy_m + 225.6),
                                         dxfattribs={'layer': 'TEXTO'})
            _attribs(ref_serie, {'Nº_SERIE_MÓDULO_CONJUNTO': serie_val}, doc)

        # Pilares (encima del todo para draw order)
        insertar_pilares(msp, x0_m, y0_m, x1_m, y1_m, blk_pil_m)

        modulos_info.append({
            'x0':x0_m,'y0':y0_m,'x1':x1_m,'y1':y1_m,
            'L':L_m,'A':A_m,'hbase':hbase_d,
            'g_carril':g_car_m,'tipo':tipo_m,'base':base_m,
            'fila':fila_m,
        })

    # ── Cotas globales del conjunto ───────────────────────────────────────────
    # Cota total L (debajo de todo el conjunto)
    y_cota_tot = y0_tot - OFS_TOT
    cota_h(msp, doc, x0_tot, y0_tot, x1_tot, y0_tot, y_cota_tot, 'PMP-T-60')

    # ── Bloques recuadros (usando bbox total y specs de fila0) ────────────────
    long_pilar0 = int(_cf(fila0,'h') or 2500) + 25
    panel0  = _cf(fila0, 'panelGrosor')
    g_car0  = grosor_carril(panel0)
    hbase0  = calc_hbase(int(_cf(fila0,'l') or 6000),
                         int(_cf(fila0,'a') or 2350),
                         _cf(fila0,'base'), panel0)
    hbase0_d = hbase0 if isinstance(hbase0, int) else (140 if "140" in str(hbase0) else 160)
    tipo0   = _tipo_tablero(_cf(fila0,'base'))

    dibujar_bloques_recuadros(
        msp, doc,
        x0_tot, y0_tot, x1_tot, y1_tot,
        hbase0_d, long_pilar0, int(_cf(fila0,'a') or 2350),
        panel0, g_car0, _cf(fila0,'panelTipo'), _cf(fila0,'serie'),
        _cf(fila0,'suministro'), tipo0, _cf(fila0,'acabado'),
        skip_serie=True)

    # ── Vista inicial ─────────────────────────────────────────────────────────
    cx_view = (MARCO_X0 + MARCO_X1) / 2.0
    cy_view = (MARCO_Y0 + MARCO_Y1) / 2.0
    doc.set_modelspace_vport(height=marco_h * 1.05, center=(cx_view, cy_view))

    doc.saveas(ruta_salida)
    print(f"  Guardado: {ruta_salida}")
