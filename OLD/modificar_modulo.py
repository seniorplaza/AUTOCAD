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
PLANTILLA_DXF  = r"C:\Users\David\Desktop\AUTOCAD\PLANTILLA.dxf"
CARPETA_SALIDA = r"C:\Users\David\Desktop\AUTOCAD\Generados"
TECNICO        = "D.P.Y."

# Punto origen del módulo dentro del marco A3
MODULO_X0 = 373364.0
MODULO_Y0 = -117207.0

# Zona a limpiar (módulo de ejemplo)
ZONA_X = (367000.0, 392000.0)
ZONA_Y = (-121500.0, -104000.0)

DIMSTYLE = "PMP-T-50"
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
    "#F5F5F5":"RAL 9002","#FFFFFF":"RAL 9010","#E8E0D5":"RAL 9001",
    "#1E213D":"RAL 5013","#6D7575":"RAL 7039",
}

def hex_a_ral(v):
    if not v: return ""
    v = v.strip()
    if "RAL" in v.upper():
        partes = v.upper().split("RAL")
        if len(partes) > 1:
            cod  = partes[1].strip().split()[0].split("-")[0]
            mate = "MATE" if "MATE" in v.upper() else ""
            return f"RAL {cod} {mate}".strip()
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
            close=True, dxfattribs={'layer':'CARRIL'})

    # Carriles verticales (izquierdo y derecho)
    # Izquierdo: x0+CARRIL_OFS_V_X  a  x0+CARRIL_OFS_V_X+grosor
    # Derecho:   x1-CARRIL_OFS_V_X-grosor  a  x1-CARRIL_OFS_V_X
    cy_ini = y0 + CARRIL_OFS_V_Y
    cy_fin = y1 - CARRIL_OFS_V_Y

    for cx_base in [x0 + CARRIL_OFS_V_X, x1 - CARRIL_OFS_V_X - grosor]:
        p = msp.add_lwpolyline(
            [(cx_base, cy_ini),(cx_base+grosor, cy_ini),(cx_base+grosor, cy_fin),(cx_base, cy_fin)],
            close=True, dxfattribs={'layer':'CARRIL'})

    print(f"  Carriles: grosor={grosor}mm")

# ─── COTAS CON DIMENSION NATIVAS ──────────────────────────────────────────────

def cota_h(msp, doc, xa, ya, xb, yb, dim_y):
    dim = msp.add_linear_dim(
        base=(xa, dim_y), p1=(xa, ya), p2=(xb, yb),
        angle=0, dimstyle=DIMSTYLE, dxfattribs={'layer':'Cotas'})
    dim.render()

def cota_v(msp, doc, xa, ya, xb, yb, dim_x):
    dim = msp.add_linear_dim(
        base=(dim_x, ya), p1=(xa, ya), p2=(xb, yb),
        angle=90, dimstyle=DIMSTYLE, dxfattribs={'layer':'Cotas'})
    dim.render()

# ─── CAJETÍN (BLOQUE CON ATRIBUTOS) ───────────────────────────────────────────

def rellenar_cajetin(doc, ob, ral, ns, suministro, fecha, oferta):
    """
    Sustituye SOLO el placeholder dentro del texto MTEXT,
    sin tocar ningún otro atributo DXF (insert, ap, width).
    Los placeholders incluyen su propio prefijo de formato en la plantilla.
    %%OB%% es el único sin prefijo -> se respeta tal cual (ap=5 centra solo).
    """
    MAPA = {
        '%%OB%%':         ob,
        '%%RAL%%':        ral,
        '%%NS%%':         ns,
        '%%SUMINISTRO%%': suministro,
        '%%FECHA%%':      fecha,
        '%%OFERTA%%':     oferta,
    }

    bloque = None
    for blk in doc.blocks:
        if 'CAJET' in blk.name.upper():
            bloque = blk
            break

    if bloque is None:
        print("  AVISO: bloque CAJETIN no encontrado en doc.blocks")
        return

    cambios = 0
    for ent in bloque:
        if ent.dxftype() not in ('MTEXT', 'TEXT'):
            continue
        texto = ent.dxf.text
        for placeholder, valor in MAPA.items():
            if placeholder in texto:
                texto = texto.replace(placeholder, str(valor))
                cambios += 1
        ent.dxf.text = texto

    print(f"  Cajetin OK ({cambios} sustituidos): OB={ob!r} RAL={ral!r} N/S={ns!r} FECHA={fecha!r} OFERTA={oferta!r}")

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
    fecha      = c("fecha") or datetime.date.today().strftime("%d/%m/%Y")

    print(f"\n  L={L}  A={A}  H={H}")
    print(f"  Base={base or 'HIDROFUGO'}  Perfil={hbase}mm  Cubierta={hcub}mm  Pilar={long_pilar}mm")
    print(f"  Pilar: '{bloque_pil}'  Correas: {len(correas)} uds  Carril: {g_carril}mm")

    doc = ezdxf.readfile(ruta_plantilla)
    msp = doc.modelspace()

    # Forzar capa CARRIL a gris (color ACI 8)
    try:
        doc.layers.get("CARRIL").dxf.color = 8
    except Exception:
        pass

    # Fuente Arial en dimstyles PMP-*
    for ds in doc.dimstyles:
        if ds.dxf.name.upper().startswith("PMP"):
            ds.dxf.dimtxsty = "ARIAL"

    # 1. Limpiar módulo de ejemplo
    limpiar_modulo(msp)

    # Coordenadas del módulo nuevo
    x0, y0 = MODULO_X0, MODULO_Y0
    x1, y1 = x0 + float(L), y0 + float(A)

    # 2. Contorno (capa PL-LIM-CASETA, color 8=gris oscuro, linetype ACAD_ISO10W100)
    cont = msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)], close=True,
                               dxfattribs={'layer':'PL-LIM-CASETA'})

    # 3. Pilares
    insertar_pilares(msp, x0, y0, x1, y1, bloque_pil)

    # 4. Correas (capa CORREAS, cian)
    for pos in correas:
        msp.add_line((x0+pos, y0), (x0+pos, y1), dxfattribs={'layer':'CORREAS'})

    # 5. Polilínea primer tablero (capa CORREAS)
    if correas:
        xt0 = x0 + correas[0]
        xt1 = xt0 + tablero
        if xt1 <= x1:
            msp.add_lwpolyline([(xt0,y0),(xt1,y0),(xt1,y1),(xt0,y1)], close=True,
                               dxfattribs={'layer':'CORREAS'})

    # 6. Carriles (capa CARRIL, gris continuo)
    dibujar_carriles(msp, x0, y0, x1, y1, g_carril)

    # 7. Cotas con DIMENSION nativas
    OFS_INF = 321
    OFS_TAB = 235
    OFS_TOT = 487
    OFS_IZQ = 321

    puntos_x = [x0] + [x0+pos for pos in correas] + [x1]
    for i in range(len(puntos_x)-1):
        xa, xb = puntos_x[i], puntos_x[i+1]
        cota_h(msp, doc, xa, y0, xb, y0, y0 - OFS_INF)

    x_tab = x0 + correas[0] if correas else x0
    while x_tab + tablero <= x1 + 5:
        cota_h(msp, doc, x_tab, y1, x_tab+tablero, y1, y1 + OFS_TAB)
        x_tab += tablero

    cota_h(msp, doc, x0, y1, x1, y1, y1 + OFS_TOT)
    cota_v(msp, doc, x0, y0, x0, y1, x0 - OFS_IZQ)

    # 8. Cajetín (bloque con atributos)
    rellenar_cajetin(doc,
        ob         = c("destino") or c("cliente") or "-",
        ral        = col_est or "-",
        ns         = c("serie") or "-",
        suministro = c("suministro") or "ARMADO",
        fecha      = fecha,
        oferta     = c("oferta") or "-",
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

def mostrar_menu(filas):
    print("\n─── PEDIDOS ───")
    for i, fila in enumerate(filas, 1):
        def c(col, f=fila):
            idx = COL.get(col,-1)
            return f[idx].strip() if 0<=idx<len(f) else ""
        print(f"  [{i}]  {c('oferta'):20}  {c('cliente'):15}  L={c('l')} A={c('a')} H={c('h')}")
    print("─────────────────")
    while True:
        try:
            sel = int(input("Numero (0=todos): "))
            if 0 <= sel <= len(filas): return sel
        except: pass

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

    if modo_todos or len(filas) == 1:
        pedidos = filas
    else:
        sel = mostrar_menu(filas)
        pedidos = filas if sel == 0 else [filas[sel-1]]

    for fila in pedidos:
        def c(col, f=fila):
            idx = COL.get(col,-1)
            return f[idx].strip() if 0<=idx<len(f) else ""
        nombre = f"{c('oferta')}_{c('serie')}".replace("/","-").replace(" ","_")
        ruta_sal = os.path.join(CARPETA_SALIDA, f"{nombre}.dxf")
        print(f"\nGenerando: {nombre}")
        generar_modulo(fila, PLANTILLA_DXF, ruta_sal)

    print(f"\n{'─'*50}\nArchivos en: {CARPETA_SALIDA}\n{'─'*50}")
    input("\nPulsa Enter para salir...")

if __name__ == "__main__":
    main()
