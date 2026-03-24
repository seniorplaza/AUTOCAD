"""
modificar_modulo.py  v5
- Abre plantilla como base (marco, cajetín bloque, fuentes, estilos)
- Borra módulo de ejemplo
- Dibuja módulo nuevo con DIMENSION nativas (dimstyle PMP-T-50)
- Correas en capa CORREAS (cian)
- Carriles en capa CARRIL (gris, línea continua) con grosor según panel
- Cajetín es bloque con atributos -> se actualiza via -ATTEDIT
"""
import sys, os, csv, datetime

try:
    import ezdxf
except ImportError:
    os.system("pip install ezdxf --break-system-packages -q")
    import ezdxf

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
# Rutas posibles de plantilla (se usa la primera que exista)
_RUTAS_PLANTILLA = [
    r"C:\Users\modulos6\Desktop\AUTOCAD\PLANTILLA.dxf",
    r"C:\Users\David\Desktop\AUTOCAD\PLANTILLA.dxf",
]
PLANTILLA_DXF = next((r for r in _RUTAS_PLANTILLA if os.path.isfile(r)), _RUTAS_PLANTILLA[0])
CARPETA_SALIDA = os.path.join(os.path.dirname(PLANTILLA_DXF), "Generados")
TECNICO        = "D.P.Y."

# Punto origen del módulo dentro del marco A3
MODULO_X0 = 373364.0
MODULO_Y0 = -117207.0

# Zona a limpiar (módulo de ejemplo)
ZONA_X = (367000.0, 392000.0)
ZONA_Y = (-121500.0, -104000.0)

DIMSTYLE = "PMP-T-50"  # se sobreescribe dinámicamente en generar_modulo()
# ──────────────────────────────────────────────────────────────────────────────

COL = {
    "fecha":0,"oferta":1,"numPedido":2,"cliente":3,"destino":4,
    "serie":5,"l":6,"a":7,"h":8,"estBase":9,"estCubierta":10,
    "estPilar":11,"panelGrosor":12,"panelTipo":13,"base":14,
    "acabado":15,"suministro":16,"perfilado":17,"colorPanel":18,
    "colorEstructura":19,"colorCarpinteria":20,"extra":21,
}

MAPA_RAL = {
    "#4E5754":"RAL 7012","#3C3F3F":"RAL 7021","#C8C2B4":"RAL 7047",
    "#F5F5F5":"BCO. PANELAIS","#FFFFFF":"RAL 9010","#E8E0D5":"RAL 9001",
    "#1E213D":"RAL 5013","#6D7575":"RAL 7039",
}

# Mapeo de código RAL a nombre comercial
MAPA_NOMBRE_RAL = {
    "9002": "BCO. PANELAIS",
}

def hex_a_ral(v):
    if not v: return ""
    v = v.strip()
    if "RAL" in v.upper():
        partes = v.upper().split("RAL")
        if len(partes) > 1:
            cod  = partes[1].strip().split()[0].split("-")[0]
            mate = "MATE" if "MATE" in v.upper() else ""
            ral_str = f"RAL {cod} {mate}".strip()
            # Sustituir por nombre comercial si existe
            return MAPA_NOMBRE_RAL.get(cod, ral_str)
        return v
    return MAPA_RAL.get(v.upper(), "")

# ─── CÁLCULOS ─────────────────────────────────────────────────────────────────

def calc_hbase(l, a, base, panel):
    try: L=int(l); A=int(a); p=int(panel) if panel else 0
    except: return 137
    t = (base or "").strip().upper()
    if t == "HORMIGONADA": return 140 if L<=7000 else 160
    if t == "TRAMEX":      return 200
    if t == "SANEAMIENTO": return 240
    v = 137 if L<=6000 else 160 if L<=8500 else 200
    if p >= 50: v = max(v, 160)
    if A > 2500: v = max(v, 160)
    return v

def calc_hcubierta(l, a, base, panel, cubierta):
    try: L=int(l); A=int(a); p=int(panel) if panel else 0
    except: return 129
    tb = (base or "").strip().upper()
    tc = (cubierta or "").strip().upper()
    if tc == "PANEL":       return 165
    if tb == "HORMIGONADA": return 160 if L<=7000 else 190
    if tb in ("TRAMEX","SANEAMIENTO"): return 160
    v = 129 if L<=6000 else 160 if L<=7000 else 190
    if p > 40: v = max(v, 160)
    if A > 2500: v = max(v, 160)
    return v

def nombre_bloque_pilar(a, panel_grosor=""):
    a = int(a)
    ancho_bloque = 2400 if a==2400 else 2440 if a==2440 else 2350
    def _fallback():
        n = ancho_bloque if ancho_bloque in (2400,2440) else 2300
        return f"PL - pilar {n}"
    try:
        p = int(panel_grosor)
        if   p <= 40: return _fallback()
        elif p <= 70: g = 60
        elif p <= 90: g = 80
        else:         g = 100
        return f"PILAR PANEL {g} ANCHO {ancho_bloque}"
    except (ValueError, TypeError):
        return _fallback()

def calc_correas(L, base_str):
    t = (base_str or "").strip().upper()
    t = t.replace("Ó","O").replace("É","E").replace("Í","I")
    inicio, paso, tablero = (710,625,1250) if "FENOL" in t else (695,610,1220)
    posiciones, x = [], inicio
    while x <= L - 5:
        posiciones.append(round(x))
        x += paso
    return posiciones, tablero

def grosor_carril(panel_grosor):
    """Devuelve el grosor del carril en mm según el grosor del panel."""
    try:
        p = int(panel_grosor)
        if   p <= 40: return 40
        elif p <= 70: return 60
        elif p <= 90: return 80
        else:         return 100
    except (ValueError, TypeError):
        return 40

# ─── LIMPIAR MÓDULO DE EJEMPLO ────────────────────────────────────────────────

def _en_zona(e):
    capas_borrar = {'PL-LIM-CASETA', 'PL-PILARES', 'CORREAS', 'CARRIL'}
    if e.dxf.layer in capas_borrar:
        return True
    if e.dxf.layer in ('0', 'Cotas'):
        t = e.dxftype()
        pts = []
        if t == 'LINE':        pts = [(e.dxf.start.x, e.dxf.start.y)]
        elif t == 'LWPOLYLINE':
            p = list(e.get_points())
            pts = [(p[0][0], p[0][1])] if p else []
        elif t == 'MTEXT':     pts = [(e.dxf.insert.x, e.dxf.insert.y)]
        elif t == 'INSERT':    pts = [(e.dxf.insert.x, e.dxf.insert.y)]
        elif t == 'DIMENSION':
            try: pts = [(e.dxf.defpoint.x, e.dxf.defpoint.y)]
            except: pass
        if pts:
            x, y = pts[0]
            return ZONA_X[0] < x < ZONA_X[1] and ZONA_Y[0] < y < ZONA_Y[1]
    return False

def limpiar_modulo(msp):
    borrar = [e for e in msp if _en_zona(e)]
    for e in borrar:
        msp.delete_entity(e)
    print(f"  Limpiadas {len(borrar)} entidades")

# ─── PILARES ──────────────────────────────────────────────────────────────────

def insertar_pilares(msp, x0, y0, x1, y1, nombre_bloque):
    for ix, iy, rot, xs in [(x0,y0,180,1),(x1,y0,180,-1),(x0,y1,0,-1),(x1,y1,0,1)]:
        msp.add_blockref(nombre_bloque, insert=(ix,iy), dxfattribs={
            'layer':'PL-PILARES','rotation':rot,'xscale':xs,'yscale':1})

# ─── CARRILES ─────────────────────────────────────────────────────────────────
#
# Geometría medida del módulo de referencia 6000x2350:
#   Carril horizontal: grosor=40, offset_x_desde_pilar=141.64, offset_y_inferior=40.22
#   Carril vertical:   grosor=40, offset_x_desde_pilar=39.64,  offset_y=170.22
#
# El grosor del carril = grosor del panel (mín 40mm)
# El offset_x_desde_pilar del carril horizontal es siempre 142 (cara interior del ala del pilar)
# El offset_x del carril vertical es siempre 40 (cara frontal del ala)

CARRIL_OFS_H_X  = 142    # offset X desde esquina del módulo al inicio del carril horizontal
CARRIL_OFS_H_Y  = 40     # offset Y desde esquina del módulo al borde exterior del carril horiz
CARRIL_OFS_V_X  = 40     # offset X desde esquina del módulo al borde exterior del carril vert
CARRIL_OFS_V_Y  = 170    # offset Y desde esquina del módulo al inicio del carril vertical

def dibujar_carriles(msp, x0, y0, x1, y1, grosor):
    """
    Dibuja los 4 carriles (2 horizontales + 2 verticales) en capa CARRIL.
    grosor: grosor del carril en mm (= grosor del panel, mín 40)
    """
    # Carriles horizontales (superior e inferior)
    # Inferior: y0+CARRIL_OFS_H_Y  a  y0+CARRIL_OFS_H_Y+grosor
    # Superior: y1-CARRIL_OFS_H_Y-grosor  a  y1-CARRIL_OFS_H_Y
    cx_ini = x0 + CARRIL_OFS_H_X
    cx_fin = x1 - CARRIL_OFS_H_X

    for cy_base in [y0 + CARRIL_OFS_H_Y, y1 - CARRIL_OFS_H_Y - grosor]:
        p = msp.add_lwpolyline(
            [(cx_ini, cy_base),(cx_fin, cy_base),(cx_fin, cy_base+grosor),(cx_ini, cy_base+grosor)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})

    # Carriles verticales (izquierdo y derecho)
    # Izquierdo: x0+CARRIL_OFS_V_X  a  x0+CARRIL_OFS_V_X+grosor
    # Derecho:   x1-CARRIL_OFS_V_X-grosor  a  x1-CARRIL_OFS_V_X
    cy_ini = y0 + CARRIL_OFS_V_Y
    cy_fin = y1 - CARRIL_OFS_V_Y

    for cx_base in [x0 + CARRIL_OFS_V_X, x1 - CARRIL_OFS_V_X - grosor]:
        p = msp.add_lwpolyline(
            [(cx_base, cy_ini),(cx_base+grosor, cy_ini),(cx_base+grosor, cy_fin),(cx_base, cy_fin)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})

    print(f"  Carriles: grosor={grosor}mm")

# ─── COTAS CON DIMENSION NATIVAS ──────────────────────────────────────────────

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

# ─── CAJETÍN (BLOQUE CON ATRIBUTOS) ───────────────────────────────────────────

def rellenar_cajetin(msp, ob, ral, ns, suministro, fecha, oferta):
    """
    Rellena los atributos del INSERT CAJETIN_VALS.
    """
    MAPA = {
        'OB':         ob,
        'RAL':        ral,
        'NS':         ns,
        'SUMINISTRO': suministro,
        'FECHA':      fecha,
        'OFERTA':     oferta,
    }
    for e in msp:
        if e.dxftype() != 'INSERT': continue
        if e.dxf.name.upper() != 'CAJETIN_VALS': continue
        cambios = 0
        for attrib in e.attribs:
            tag = attrib.dxf.tag.upper()
            if tag in MAPA:
                attrib.dxf.text = str(MAPA[tag])
                cambios += 1
        print(f"  Cajetin OK ({cambios} atributos): OB={ob!r} RAL={ral!r} N/S={ns!r} FECHA={fecha!r} OFERTA={oferta!r}")
        return
    print("  AVISO: INSERT CAJETIN_VALS no encontrado")

# ─── GENERACIÓN ───────────────────────────────────────────────────────────────

def generar_modulo(fila, ruta_plantilla, ruta_salida):
    def c(col):
        idx = COL.get(col,-1)
        return fila[idx].strip() if 0<=idx<len(fila) else ""

    L     = int(c("l")  or 6000)
    A     = int(c("a")  or 2350)
    H     = int(c("h")  or 2500)
    base  = c("base")
    panel = c("panelGrosor")

    hbase      = calc_hbase(L, A, base, panel)
    hcub       = calc_hcubierta(L, A, base, panel, c("suministro"))
    long_pilar = H - hbase - hcub
    bloque_pil = nombre_bloque_pilar(A, panel)
    correas, tablero = calc_correas(L, base)
    g_carril   = grosor_carril(panel)
    col_est    = hex_a_ral(c("colorEstructura"))
    # Normalizar fecha a DD/MM/YYYY (con ceros)
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

    # Forzar capa CARRIL a gris (color ACI 8)
    try:
        doc.layers.get("CARRIL").dxf.color = 8    # gris
    except Exception:
        pass
    try:
        doc.layers.get("CORREAS").dxf.color = 4   # azul
    except Exception:
        pass

    # Crear dimstyles PMP-T-50 y PMP-T-60 si no existen, basados en PMP-T-75
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
        # Forzar Arial
        if doc.dimstyles.has_entry(nombre):
            doc.dimstyles.get(nombre).dxf.dimtxsty = 'ARIAL'
    if ds75:
        ds75.dxf.dimtxsty = 'ARIAL'
    dimstyle_usar = 'PMP-T-75'  # fallback

    # 1. Limpiar módulo de ejemplo
    limpiar_modulo(msp)

    # Coordenadas del módulo nuevo
    # Marco cajetín: proporciones A3 (ratio 7110/5028 = 1.414)
    MARCO_BASE_X0 = 393890.0
    MARCO_BASE_Y0 = -111189.4
    RATIO_A3 = 7110.0 / 5028.0
    MARGEN_X = 1220.0
    MARGEN_Y = 400.0

    # Tamaño mínimo: nunca menor que A3 base (7110x5028)
    A3_W, A3_H = 7110.0, 5028.0
    w_min = max(float(L) + 2 * MARGEN_X, A3_W)
    h_min = max(float(A) + 2 * MARGEN_Y, A3_H)

    # Escalar manteniendo proporción A3
    if w_min / h_min > RATIO_A3:
        marco_w = w_min
        marco_h = marco_w / RATIO_A3
    else:
        marco_h = h_min
        marco_w = marco_h * RATIO_A3

    MARCO_X0 = MARCO_BASE_X0
    MARCO_Y0 = MARCO_BASE_Y0
    MARCO_X1 = MARCO_X0 + marco_w
    MARCO_Y1 = MARCO_Y0 + marco_h

    # Escalar el bloque CAJETIN_VALS
    BLOQUE_W, BLOQUE_H = 7109.9, 5027.7
    sx = marco_w / BLOQUE_W
    sy = marco_h / BLOQUE_H

    blk_def = doc.blocks.get('CAJETIN_VALS')
    # Coordenadas locales originales de cada ATTDEF
    attdefs = {a.dxf.tag: a for a in blk_def if a.dxftype() == 'ATTDEF'}

    # INSERT_ORIG es donde estaba el INSERT en la plantilla base
    INSERT_ORIG_X, INSERT_ORIG_Y = 393890.0, -111189.4

    for ent in msp:
        if ent.dxftype() == 'INSERT' and 'CAJET' in ent.dxf.name.upper():
            ent.dxf.xscale = sx
            ent.dxf.yscale = sy
            ent.dxf.insert = (MARCO_X0, MARCO_Y0, 0)
            # Recalcular posición mundo de cada atributo:
            # mundo = INSERT_nuevo + local * escala
            for att in ent.attribs:
                if att.dxf.tag in attdefs:
                    ad = attdefs[att.dxf.tag]
                    att.dxf.insert = (
                        MARCO_X0 + ad.dxf.insert.x * sx,
                        MARCO_Y0 + ad.dxf.insert.y * sy,
                        0
                    )
                    att.dxf.height = ad.dxf.height * min(sx, sy)
            break

    # Centrar módulo en el nuevo marco
    AREA_CX = (MARCO_X0 + MARCO_X1) / 2.0
    AREA_CY = (MARCO_Y0 + MARCO_Y1) / 2.0
    x0 = AREA_CX - float(L) / 2.0
    y0 = AREA_CY - float(A) / 2.0
    x1, y1 = x0 + float(L), y0 + float(A)

    # 2. Contorno (capa PL-LIM-CASETA, color 8=gris oscuro, linetype ACAD_ISO10W100)
    cont = msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], close=True,
                               dxfattribs={'layer':'PL-LIM-CASETA'})

    # 3. Pilares
    insertar_pilares(msp, x0, y0, x1, y1, bloque_pil)

    # 4. Correas (capa CORREAS, cian)
    for pos in correas:
        msp.add_line((x0+pos, y0), (x0+pos, y1), dxfattribs={'layer':'CORREAS', 'color':4})

    # 5. Polilínea tablero eliminada (solo se dibujan las líneas de correas)

    # 6. Carriles (capa CARRIL, gris continuo)
    dibujar_carriles(msp, x0, y0, x1, y1, g_carril)

    # 7. Cotas con DIMENSION nativas
    OFS_INF = 321
    # Nombre del tipo de tablero para la cota
    _base_upper = (base or '').strip().upper().replace('Ó','O').replace('É','E').replace('Í','I')
    tipo_tablero = 'Fenólico' if 'FENOL' in _base_upper else 'Hidrófugo'

    OFS_TAB = 235
    OFS_TOT = 487
    OFS_IZQ = 321

    # Cotas inferiores entre correas (PMP-T-50)
    puntos_x = [x0] + [x0+pos for pos in correas] + [x1]
    for i in range(len(puntos_x)-1):
        xa, xb = puntos_x[i], puntos_x[i+1]
        cota_h(msp, doc, xa, y0, xb, y0, y0 - OFS_INF, 'PMP-T-50')

    # Cotas de tableros arriba: x0 + carril_izq + 5mm hasta x1 - carril_der - 5mm
    if correas:
        x_tab_ini     = x0 + CARRIL_OFS_V_X + g_carril + 5   # x0+80+5
        x_tab_fin_max = x1 - CARRIL_OFS_V_X - g_carril - 5   # x1-80-5
        x_tab = x_tab_ini
        while x_tab < x_tab_fin_max:
            fin = min(x_tab + tablero, x_tab_fin_max)
            cota_h(msp, doc, x_tab, y1, fin, y1, y1 + OFS_TAB, 'PMP-T-50', tipo_tablero)
            x_tab += tablero

    # Cota largo total arriba (PMP-T-60)
    cota_h(msp, doc, x0, y1, x1, y1, y1 + OFS_TOT, 'PMP-T-60')
    # Cota ancho izquierda (PMP-T-60)
    cota_v(msp, doc, x0, y0, x0, y1, x0 - OFS_IZQ, 'PMP-T-60')

    # 8. Cajetín (bloque con atributos)
    rellenar_cajetin(msp,
        ob         = c("destino") or c("cliente") or "-",
        ral        = col_est or "-",
        ns         = c("serie") or "-",
        suministro = c("suministro") or "ARMADO",
        fecha      = fecha,
        oferta     = c("numPedido") or c("oferta") or "-",
    )

    # 9. Guardar
    doc.saveas(ruta_salida)
    print(f"  Guardado: {ruta_salida}")

# ─── CSV ──────────────────────────────────────────────────────────────────────

def leer_csv(ruta):
    filas = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for i, fila in enumerate(csv.reader(f, delimiter=";")):
            if i == 0: continue
            if any(campo.strip() for campo in fila):
                filas.append(fila)
    return filas

def _c(fila, col):
    idx = COL.get(col, -1)
    return fila[idx].strip() if 0 <= idx < len(fila) else ""

def _clave_pedido(fila):
    """Agrupa módulos del mismo pedido por Número de Pedido."""
    return _c(fila, 'numPedido')

def mostrar_menu(grupos):
    """
    grupos: lista de (clave, [filas])
    Muestra un pedido por línea. Si tiene >1 módulo, pide subselección M1/M2/...
    Devuelve lista de filas a generar.
    """
    print("\n─── PEDIDOS ───")
    for i, (clave, filas_g) in enumerate(grupos, 1):
        numpedido = clave
        f0 = filas_g[0]
        cliente = _c(f0, 'cliente')
        if len(filas_g) == 1:
            f = filas_g[0]
            print(f"  [{i:>2}]  {numpedido:15}  {cliente:15}  L={_c(f,'l')} A={_c(f,'a')} H={_c(f,'h')}")
        else:
            print(f"  [{i:>2}]  {numpedido:15}  {cliente:15}  ({len(filas_g)} módulos)")
            for j, f in enumerate(filas_g, 1):
                notas = _c(f,'extra') or ''
                print(f"         M{j}  L={_c(f,'l')} A={_c(f,'a')} H={_c(f,'h')}  Serie={_c(f,'serie')}  {notas}")
    print("─────────────────")

    while True:
        try:
            sel = int(input("Número de pedido (0=todos): "))
        except (ValueError, EOFError):
            continue
        if sel == 0:
            # Todos los módulos de todos los pedidos
            return [f for _, filas_g in grupos for f in filas_g]
        if 1 <= sel <= len(grupos):
            clave, filas_g = grupos[sel - 1]
            # Si hay múltiples variantes se generan todas (M1, M2...)
            return filas_g

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    modo_todos = "--todos" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        ruta_csv = args[0]
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            ruta_csv = filedialog.askopenfilename(
                title="Selecciona el CSV del Gestor",
                filetypes=[("CSV","*.csv"),("Todos","*.*")])
            root.destroy()
        except:
            ruta_csv = input("Ruta CSV: ").strip().strip('"')

    if not ruta_csv or not os.path.isfile(ruta_csv):
        print("CSV no encontrado."); input(); sys.exit(1)

    if not os.path.isfile(PLANTILLA_DXF):
        print(f"No encuentro: {PLANTILLA_DXF}"); input(); sys.exit(1)

    filas = leer_csv(ruta_csv)
    if not filas:
        print("CSV vacio."); input(); sys.exit(1)

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # Agrupar filas por pedido (oferta+numPedido+destino), preservando orden
    from collections import OrderedDict
    grupos_dict = OrderedDict()
    for fila in filas:
        clave = _clave_pedido(fila)
        grupos_dict.setdefault(clave, []).append(fila)
    grupos = list(grupos_dict.items())

    if modo_todos:
        pedidos = filas
    elif len(filas) == 1:
        pedidos = filas
    else:
        pedidos = mostrar_menu(grupos)

    # Contar cuántas veces aparece cada numPedido en la selección
    from collections import Counter
    conteo = Counter(_c(f, 'numPedido') for f in pedidos)

    contadores = {}
    for fila in pedidos:
        np = _c(fila, 'numPedido')
        base = f"{np}-{_c(fila,'destino')}".replace("/","-").replace(" ","_")
        if conteo[np] > 1:
            contadores[np] = contadores.get(np, 0) + 1
            nombre = f"{base}-M{contadores[np]}"
        else:
            nombre = base
        ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
        print(f"\nGenerando: {nombre}")
        generar_modulo(fila, PLANTILLA_DXF, ruta_sal)

    print(f"\n{chr(9472)*50}\nArchivos en: {CARPETA_SALIDA}\n{chr(9472)*50}")
    input("\nPulsa Enter para salir...")

if __name__ == "__main__":
    main()
