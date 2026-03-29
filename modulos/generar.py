"""
generar.py — Función principal de generación de un DXF por fila del CSV.
Lee la plantilla, limpia el ejemplo, posiciona el módulo y llama a todos los submódulos.
"""
import datetime
import ezdxf
from ezdxf.enums import TextEntityAlignment

from .config      import COL, CARPETA_SALIDA
from .calculos    import calc_hbase, calc_hcubierta, nombre_bloque_pilar, grosor_carril, calc_correas, hex_a_ral
from .limpiar     import limpiar_modulo
from .dxf_utils   import cota_h, cota_v, _attribs
from .plano_base  import insertar_pilares, dibujar_carriles, dibujar_alzado_base, dibujar_fleje
from .seccion_ancho import dibujar_seccion_ancho
from .bloques     import dibujar_bloques_recuadros
from .config      import CARRIL_OFS_V_X, CARRIL_OFS_H_Y


def generar_modulo(fila, ruta_plantilla, ruta_salida):
    def c(col):
        idx = COL.get(col, -1)
        return fila[idx].strip() if 0 <= idx < len(fila) else ""

    L     = int(c("l")  or 6000)
    A     = int(c("a")  or 2350)
    H     = int(c("h")  or 2500)
    base  = c("base")
    panel = c("panelGrosor")

    modulo    = c("modulo") or "M1"
    cantidad  = int(c("cantidad") or 1)
    conjunto  = c("conjunto").strip().lower() == "true"
    import json as _json
    try:
        adosamiento = _json.loads(c("adosamiento")) if c("adosamiento") else None
    except Exception:
        adosamiento = None

    hbase      = calc_hbase(L, A, base, panel)
    hcub       = calc_hcubierta(L, A, base, panel, c("cubierta"))
    long_pilar = H + 25
    bloque_pil = nombre_bloque_pilar(A, panel)
    g_carril   = grosor_carril(panel)
    correas, tablero = calc_correas(L, base, A, g_carril)
    col_est    = hex_a_ral(c("colorEstructura"))

    _fecha_raw = c("fecha") or datetime.date.today().strftime("%d/%m/%Y")
    try:
        _d, _m, _y = _fecha_raw.strip().split("/")
        fecha = f"{int(_d):02d}/{int(_m):02d}/{_y}"
    except Exception:
        fecha = _fecha_raw

    print(f"\n  L={L}  A={A}  H={H}")
    print(f"  Base={base or 'HIDROFUGO'}  Perfil={hbase}mm  Cubierta={hcub}mm  Pilar={long_pilar}mm")
    print(f"  Pilar: '{bloque_pil}'  Correas: {len(correas)} uds  Carril: {g_carril}mm")

    doc = ezdxf.readfile(ruta_plantilla)
    msp = doc.modelspace()

    # Forzar colores de capas
    try: doc.layers.get("CARRIL").dxf.color  = 8
    except: pass
    try: doc.layers.get("CORREAS").dxf.color = 4
    except: pass

    # Crear dimstyles PMP-T-50 y PMP-T-60 basados en PMP-T-75
    ATTRS_PMP = ['dimtxt','dimasz','dimexo','dimexe','dimdli','dimdle',
                 'dimtad','dimtih','dimtoh','dimgap','dimblk','dimblk1','dimblk2','dimsah','dimdec']
    ds75 = doc.dimstyles.get('PMP-T-75')
    for nombre, escala in [('PMP-T-50', 50.0), ('PMP-T-60', 60.0)]:
        if not doc.dimstyles.has_entry(nombre) and ds75 is not None:
            ds_new = doc.dimstyles.new(nombre)
            ds_new.dxf.dimscale = escala
            for attr in ATTRS_PMP:
                try: setattr(ds_new.dxf, attr, getattr(ds75.dxf, attr))
                except: pass
        if doc.dimstyles.has_entry(nombre):
            doc.dimstyles.get(nombre).dxf.dimtxsty = 'ARIAL'
    if ds75:
        ds75.dxf.dimtxsty = 'ARIAL'

    # 1. Limpiar módulo de ejemplo
    limpiar_modulo(msp)

    # ── Marco A3 dinámico ───────────────────────────────────────────────────────
    MARCO_BASE_X0   = 393890.0
    MARCO_BASE_Y0   = -111189.4
    RATIO_A3        = 7110.0 / 5028.0
    MARGEN_X        = 1550.0
    MARGEN_Y_SUP    = 450.0
    OFS_COR_BOT     = 321.0     # espacio que ocupan las cotas debajo del módulo
    _ESPACIO_ENCIMA = 3009.6 + MARGEN_Y_SUP

    A3_W, A3_H  = 7110.0, 5028.0
    # Altura mínima: contenido total (cotas inf + módulo + todo encima) + margen simétrico
    contenido_h = OFS_COR_BOT + float(A) + _ESPACIO_ENCIMA
    h_min = max(contenido_h + 2 * OFS_COR_BOT, A3_H)   # margen inf ≈ margen sup
    w_min = max(float(L) + 2 * MARGEN_X, A3_W)
    if w_min / h_min > RATIO_A3:
        marco_w = w_min;    marco_h = marco_w / RATIO_A3
    else:
        marco_h = h_min;    marco_w = marco_h * RATIO_A3

    # Margen inferior dinámico: centra el contenido verticalmente en el marco
    # Contenido real: desde (y0 - OFS_COR_BOT) hasta (y1 + 3009.6)
    # → total_real = OFS_COR_BOT + A + 3009.6  (sin MARGEN_Y_SUP)
    total_real   = OFS_COR_BOT + float(A) + 3009.6
    MARGEN_Y_INF = OFS_COR_BOT + (marco_h - total_real) / 2.0

    MARCO_X0 = MARCO_BASE_X0
    MARCO_Y0 = MARCO_BASE_Y0
    MARCO_X1 = MARCO_X0 + marco_w
    MARCO_Y1 = MARCO_Y0 + marco_h

    # ── Cajetín escalado ────────────────────────────────────────────────────────
    BLOQUE_W, BLOQUE_H = 7109.9, 5027.7
    sx = marco_w / BLOQUE_W
    sy = marco_h / BLOQUE_H

    _caj_vals = {
        'OB':         c("destino") or c("cliente") or "-",
        'RAL':        col_est or "-",
        'NS':         c("serie") or "-",
        'SUMINISTRO': c("suministro") or "ARMADO",
        'FECHA':      fecha,
        'OFERTA':     c("numPedido") or c("oferta") or "-",
        'D.P.Y.':     'D.P.Y.',
        'REV-0':      'REV-0',
    }
    blk_def = doc.blocks.get('CAJETIN_VALS')
    for ent in blk_def:
        if ent.dxftype() == 'ATTDEF':
            tag = ent.dxf.tag.upper()
            if tag in _caj_vals:
                ent.dxf.text = str(_caj_vals[tag])

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

    print(f"  Cajetin OK: OB={_caj_vals['OB']!r} RAL={_caj_vals['RAL']!r} "
          f"N/S={_caj_vals['NS']!r} FECHA={_caj_vals['FECHA']!r} OFERTA={_caj_vals['OFERTA']!r}")

    # ── Coordenadas del módulo ──────────────────────────────────────────────────
    AREA_CX = (MARCO_X0 + MARCO_X1) / 2.0
    x0 = AREA_CX - float(L) / 2.0
    y0 = MARCO_Y0 + MARGEN_Y_INF
    x1, y1 = x0 + float(L), y0 + float(A)

    # 2. Contorno
    msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], close=True,
                       dxfattribs={'layer':'PL-LIM-CASETA'})

    # 4. Correas (líneas cian)
    for pos in correas:
        msp.add_line((x0+pos, y0), (x0+pos, y1), dxfattribs={'layer':'CORREAS', 'color':4})

    # 6. Carriles
    dibujar_carriles(msp, x0, y0, x1, y1, g_carril, A)

    # 7. Cotas
    _base_upper = (base or '').strip().upper().replace('Ó','O').replace('É','E').replace('Í','I')
    if 'FIBRO' in _base_upper:
        tipo_tablero = 'Fibrocemento'
    elif 'FENOL' in _base_upper:
        tipo_tablero = 'Fenólico'
    else:
        tipo_tablero = 'Hidrófugo'

    OFS_COR_BOT = 321;  OFS_TOT = 587;  OFS_TAB = 270;  OFS_IZQ = 321

    puntos_x = [x0] + [x0+pos for pos in correas] + [x1]
    for i in range(len(puntos_x)-1):
        cota_h(msp, doc, puntos_x[i], y0, puntos_x[i+1], y0, y0-OFS_COR_BOT, 'PMP-T-50')

    cota_h(msp, doc, x0, y1, x1, y1, y1+OFS_TOT, 'PMP-T-60')

    if correas:
        x_tab_ini     = x0 + CARRIL_OFS_V_X + g_carril + 5
        x_tab_fin_max = x1 - CARRIL_OFS_V_X - g_carril - 5
        span = x_tab_fin_max - x_tab_ini
        n_full = int(span // tablero)
        if n_full > 0:
            partial_tab = span - n_full * tablero
            if partial_tab <= tablero / 2:
                # Partial estrecho → centrar
                if partial_tab < tablero / 2:
                    n_full -= 1
                    partial_tab = span - n_full * tablero
                first = x_tab_ini + partial_tab / 2.0
                if partial_tab / 2.0 > 1:
                    cota_h(msp, doc, x_tab_ini, y1, first, y1, y1+OFS_TAB, 'PMP-T-50', tipo_tablero)
                for i in range(n_full):
                    cota_h(msp, doc, first + i*tablero, y1, first + (i+1)*tablero, y1, y1+OFS_TAB, 'PMP-T-50', tipo_tablero)
                last = first + n_full * tablero
                if x_tab_fin_max - last > 1:
                    cota_h(msp, doc, last, y1, x_tab_fin_max, y1, y1+OFS_TAB, 'PMP-T-50', tipo_tablero)
            else:
                # Partial grande → izquierda
                x_tab = x_tab_ini
                while x_tab < x_tab_fin_max:
                    fin = min(x_tab + tablero, x_tab_fin_max)
                    cota_h(msp, doc, x_tab, y1, fin, y1, y1+OFS_TAB, 'PMP-T-50', tipo_tablero)
                    x_tab += tablero
        else:
            cota_h(msp, doc, x_tab_ini, y1, x_tab_fin_max, y1, y1+OFS_TAB, 'PMP-T-50', tipo_tablero)

    # 8. Elementos alzado, sección y bloques
    hbase_draw = hbase if isinstance(hbase, int) else (140 if "140" in str(hbase) else 160)
    dibujar_alzado_base(msp, doc, x0, y0, x1, y1, hbase_draw, correas, tipo_tablero, long_pilar, A, g_carril)
    from .plano_base import TABLERO_LARGO
    largo_tab    = TABLERO_LARGO.get(tipo_tablero, 2440)
    span_tablero = A - 2 * (CARRIL_OFS_H_Y + g_carril)
    hay_fleje    = span_tablero > largo_tab
    # Cota A: más a la izquierda si hay fleje (para dejar espacio a las sub-cotas)
    ofs_cota_a = OFS_IZQ + 200 if hay_fleje else OFS_IZQ
    cota_v(msp, doc, x0, y0, x0, y1, x0 - ofs_cota_a, 'PMP-T-60')
    if hay_fleje:
        dibujar_fleje(msp, doc, x0, y0, x1, y1, g_carril, tipo_tablero, x_cota=x0 - OFS_IZQ + 110)
    dibujar_seccion_ancho(msp, doc, x0, y0, x1, y1, hbase_draw, g_carril, tipo_tablero, L, base)
    dibujar_bloques_recuadros(msp, doc, x0, y0, x1, y1, hbase_draw, long_pilar, A,
                              panel, g_carril, c("panelTipo"), c("serie"), c("suministro"),
                              tipo_tablero, c("acabado"))

    # 9. Pilares al final → draw order encima de todo
    insertar_pilares(msp, x0, y0, x1, y1, bloque_pil)

    # 10. Vista inicial centrada en el marco A3 general
    cx_view = (MARCO_X0 + MARCO_X1) / 2.0
    cy_view = (MARCO_Y0 + MARCO_Y1) / 2.0
    doc.set_modelspace_vport(height=marco_h * 2.5, center=(cx_view, cy_view - marco_h/2))

    # 11. PLANO DE CUBIERTA
    from .cubierta import dibujar_estructura_cubierta
    Y_CUBIERTA = MARCO_Y0 - marco_h - 2000  # Espacio entre planos
    dibujar_estructura_cubierta(msp, doc, fila, Y_CUBIERTA)

    # 12. Guardar
    doc.saveas(ruta_salida)
    print(f"  Guardado: {ruta_salida}")
