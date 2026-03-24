"""
modificar_modulo.py  v7
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXTO GENERAL DEL PROYECTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script Python para generación automática de planos DXF de módulos prefabricados.
Lee un CSV exportado desde el gestor de pedidos (gestor.html) y una PLANTILLA.dxf,
y genera un DXF por pedido con TODOS los planos apilados verticalmente en el
modelspace (uno debajo de otro, con separación entre ellos).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANOS A GENERAR (apilados en modelspace, misma PLANTILLA.dxf para todos)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ESTRUCTURA BASE (implementado - v7)
   ── Planta del módulo ──────────────────────────────────────────────────────
   - Contorno módulo (capa PL-LIM-CASETA)
   - Pilares en esquinas (capa PL-PILARES) - bloque según ancho y grosor panel
   - Correas (capa CORREAS, cian) - posición según tipo tablero (Fenólico/Hidrófugo)
   - Carriles (capa CARRIL, gris) - grosor según panel, longitud según ancho módulo
   - Cotas nativas DXF (dimstyle PMP-T-50 entre correas, PMP-T-60 totales)
   - Cajetín con atributos: OB, RAL, N/S, SUMINISTRO, FECHA, OFERTA

   ── Alzado de la base (encima del módulo) ─────────────────────────────────
   - Rectángulo verde (capa ALZ-EST-BA-DIB): ancho = L módulo, alto = hbase mm
     · hbase calculado con calc_hbase() según tipo base y dimensiones del CSV
     · Offset desde top del módulo: 1186mm al borde inferior, 1186+hbase al superior
   - Rectángulos de correas en alzado (capa ALZ-CER-DIB): 120×100mm
     · Centrados en el eje de cada correa (mismas X que las líneas CORREAS en planta)
     · Offset vertical desde top: 1218mm al borde inferior, +100mm al superior
     · Línea horizontal adicional de x1 hasta la primera correa (tapa del alzado)
   - Líneas de eje verticales (capa Ejes, color 8 gris):
     · Una línea por cada correa, de y0 a y1 del módulo, en la X de la correa
   - Cotas PMP-T-60 entre correas: defpoint a 270mm sobre top del módulo
     · Miden el espacio entre cada par de correas consecutivas (y bordes)
   - Cota vertical PMP-T-75 del hbase: dx=-218mm desde x0 del módulo
     · Mide la altura del rectángulo ALZ-EST-BA-DIB (= hbase mm)
   - Rectángulo redondeado "PERFIL BASE" (capa Cotas, bulge=-0.414 = arco 90°):
     · Posición: x1-1038 hasta x1, entre dy=803 y dy=1015 sobre y1
     · Radio de esquinas ~40mm. Texto interior "PERFIL BASE Xmm" en dx=5028, dy=880
   - Cajas de texto (LWPOLYLINE color 5 azul, capa TEXTO):
     · Caja MUÑONES: dx_x0=[1718, 3032], dy_top=[1681, 1865]
     · Caja PILARES: dx_x0=[3149, 4615], dy_top=[1681, 1865]
   - Textos dinámicos encima del módulo (capa TEXTO):
     · "MUÑONES Xx×Yymm." en dx=1758, dy=1741
     · "PILARES Xx×Yy×Hmm"  en dx=3189, dy=1741
       Dimensiones del pilar según ancho A: A≤2350 → 195×167, A≤2400/2440 → 220×192
       Muñón = pilar - 20mm en cada dimensión (ej: 195×167 → muñón 175×147)
       La H del pilar = long_pilar = H_modulo - hbase - hcubierta
     · "*COMPROBAR LA MEDIDA DEL TABLERO ANTES DE SOLDAR"       dx=1616, dy=2349
     · "*COMPROBAR LAS DIMENSIONES DE LOS MUÑONES CON LOS PILARES" dx=1616, dy=2093
     · "DISTRIBUCIÓN CORREAS BASE C/ HIDRÓFUGO|FENÓLICO"        dx=1744, dy=2807
       (tipo determinado del campo 'base' del CSV)

   ── Zona derecha del módulo ────────────────────────────────────────────────
   - Sección del carril vertical (geometría fija, offsets desde x1 del módulo):
     · CUADROS (franja estrecha borde):      dx=[270,289], altura = A módulo ±20
     · CORREAS (cuerpo del carril):          dx=[291, 291+g_carril+62], dy=[+82, A-82]
     · PL-CER-DIB superior e inferior:      dx=[289,429], h=105mm, en borde top y bot
       Con líneas de detalle del encuentro carril-pilar
     · PL-CER-DIB detalle panel alejado:    dx=[981,1191] desde x1, en borde inferior
       + CORREAS detalle (dx=[675,1024]) + CUADROS rótulo (dx=[658,1031])
   - Círculo de referencia (capa Cotas, r=130mm): dx=371, cy=y0+59
   - Líneas de referencia (capa Cotas)
   - MTEXT "Aglomerado\nHidrófugo 19mm" o "Aglomerado\nFenólico 18mm":
     · dx_x1=1365, dy_top=-1454  (a la derecha del módulo, a media altura)
     · Hidrófugo = 19mm grosor | Fenólico = 18mm grosor

   ── Dentro del módulo ──────────────────────────────────────────────────────
   - HATCH sólido verde (color 3, capa SOMBRAS): representa el tablero
     · Rect redondeado r=50mm centrado en L/2, semiancho=480mm (representativo)
     · dy_top desde y1: borde sup=-844mm, borde inf=-1118mm
   - Contorno amarillo del tablero (LWPOLYLINE color 2, capa Cotas):
     · Mismo rect redondeado que el HATCH, r=50mm
   - MTEXT "TIPO + ACABADO" centrado en módulo, dy_bot=994mm desde y0
   - MTEXT serie centrado en módulo, dy_bot=1369mm desde y0

2. ESTRUCTURA CUBIERTA (pendiente)
   - Vista en planta: contorno + correas OMEGA con etiqueta tipo encima de cada una
   - Cotas entre correas y totales (en rojo)
   - Texto "DISTRIBUCIÓN CUBIERTA"
   - Texto "X UD EN KIT" + rango de series (del CSV campo Serie)
   - Bloque fijo plantilla: perspectiva cara larga del módulo
   - Bloque fijo plantilla: corte perspectiva cara corta (capas: VIERTE AGUAS,
     CHAPA TRAPE. 6G x2, FALSO TECHO, AISLAMIENTO, CORREA OMEGA)
   - Bloque fijo plantilla: detalle sección correas
   - Tipo OMEGA de cada correa (40/50/...) según tabla pendiente de recibir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS IMPORTANTES (aclaradas/corregidas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LONGITUD DEL PILAR:
  - Los campos L, A, H del CSV son LARGO, ANCHO y ALTURA INTERIOR del módulo.
  - El pilar siempre mide H_interior + 25mm (el pilar sobresale 25mm del módulo).
  - Ejemplos: H=2500 -> pilar=2525mm | H=2300 -> pilar=2325mm | H=3000 -> pilar=3025mm
  - NO depende de hbase ni hcubierta.

ALTURA PERFIL BASE (hbase):
  - "BASE AISLADA e40 / CARRIL > e50" en la tabla significa panel > 50mm
    (carril mayor que e50, es decir panel de 60mm o más).
  - Panel exactamente de 50mm usa carril e50 -> hbase NO sube a 160mm.
  - La condición es p > 50 (no >= 50).

PLANO ESTRUCTURA CUBIERTA (pendiente):
  - La hcubierta (calc_hcubierta) NO interviene en ningún cálculo del plano de base.
  - Se usará en el futuro para el plano de estructura cubierta.

MÓDULOS ADOSADOS (TAPAR CARRIL):
  - Cuando dos módulos se acoplan lateralmente, el carril interior queda visible.
  - Se tapa con tablero hidrófugo o fenólico → en el plano aparece el bloque
    'CORTE CARRIL CARA LARGA' (dos inserts enfrentados a la derecha del módulo).
  - Por ahora se inserta siempre; en el futuro se condicionará al tipo de suministro.

3. DISTRIBUCIÓN DE PANELES (pendiente - complejo, depende de plano base)
   - Vista en planta con pilares, paneles en 4 caras, carpintería
   - Título: "DISTRIBUCIÓN DE PANELES / PANEL AxBxGmm"
   - Texto central: tipo suelo + acabado (ej: "HIDRÓFUGO + SINTASOL")
   - Cotas totales en rojo
   - Leyenda carpintería (tabla con P1, V1, etc.)
   - LÓGICA PANELES EXTERIORES:
     · Pilar H=2300 (H interior 2275): panel exterior 2337mm alto
     · Pilar H=2525 (H interior 2500): panel exterior 2565mm alto
     · Panel interior (si lo hay): 2270mm (H2275) o 2495mm (H2500)
     · Ancho estándar panel: 1000mm, pero último panel del hueco ajusta
     · Panel sobre puerta: 265x1000xG (H int 2275) o 490x1000xG (H int 2500)
     · Paneles sobre y bajo ventana con medidas propias
   - LÓGICA MACHO/HEMBRA: depende de apertura puerta (izq/dcha) - pendiente definir
   - CARPINTERÍA: posición viene del plano base de referencia - pendiente definir flujo
   - Puede haber: puertas exteriores, puertas interiores, ventanas (cantidad variable)

4. PLANO DE REVISIÓN (pendiente - lógica definida)
   - Idéntico al plano de DISTRIBUCIÓN DE PANELES pero simplificado:
     · SIN cotas de paneles ni anotaciones de medidas
     · CON contorno, pilares, carpintería, paneles dibujados
     · CON leyenda carpintería y texto central (suelo+acabado)

5. PLANO DE ELECTRICIDAD (pendiente - lógica parcialmente definida)
   - DOS vistas del mismo módulo apiladas verticalmente:
     · ARRIBA: plano de ALUMBRADO (luminarias, interruptores)
     · ABAJO:  plano de FUERZA (enchufes, termo, AC, RJ45, preinstalaciones...)
   - Cada vista incluye: contorno, pilares, carpintería, paneles (como referencia)
   - Elementos eléctricos (capa PL-ELECTRICIDAD): enchufes 16A, interruptores,
     pantallas LED, etc. — posición viene del plano base de referencia
   - Fontanería visible también (termo, fregadero) en capa PL-FONTANERIA
   - Esquema unifilar a la izquierda: varía según instalación del cliente
     (acometida, diferenciales, PIAs alumbrado/usos varios/termo) - lógica pendiente
   - Textos de altura de montaje (H=900mm, H=1100mm, H=1900mm...)
   - Texto fijo: "INSTALACIÓN ELÉCTRICA CABLE LIBRE HALÓGENO..."
   - Bloques en plantilla: enchufe 16A, interruptor, pantalla 2x18W led,
     cuadro+acometida, termo, fregadeo+escurridor, panel 40, PL-puerta 1H,
     PL-ventana 500, PL-ventana 500 reja, VENTANA 2000X1200, VENTANA 1800

6. PLANO DE SANEAMIENTO Y FONTANERÍA (pendiente - lógica parcialmente definida)
   - Solo se genera si el módulo lleva instalación de saneamiento/fontanería
   - UN módulo apilado por cada unidad del pedido (con su N/S encima, capa NºMÓDULOS)
   - Cada vista incluye: contorno, pilares, paneles, carpintería (como referencia)
   - Capas específicas:
     · A.FRIA:              tuberías agua fría
     · CALIENTE:            tuberías agua caliente
     · tubo sanitari 3 pvc: evacuación PVC Ø40mm y Ø110mm, codos, salidas
     · PL-FONTANERIA:       aparatos (inodoro, lavabo, fregadero, termo con capacidad)
   - Posición aparatos sanitarios: viene del plano base de referencia
   - Recorrido de tuberías: actualmente se dibuja a mano - pendiente definir automatización
   - Textos descriptivos: "EVACUACION PVC ØXXmm POR PANEL",
     "INSTALACION SANEAMIENTO", "FONTANERIA: AGUA FRIA / AGUA CALIENTE",
     "LINEA GENERAL Ø22mm", "ACOMETIDA MACHO 3/4""
   - Notas técnicas (tipo ducha, grifo pulsador, etc.): varían por proyecto - pendiente
   - Bloques en plantilla: inodoro, lavabo, fregadeo+escurridor, termo,
     Salisa saneamiento 110, codo245

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUCTURA DEL CSV (separador ";", encoding utf-8-sig)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Col 0  fecha           | Col 1  oferta          | Col 2  numPedido
Col 3  cliente         | Col 4  destino         | Col 5  serie
Col 6  l (largo mm)    | Col 7  a (ancho mm)    | Col 8  h (alto mm)
Col 9  estBase         | Col 10 estCubierta     | Col 11 estPilar
Col 12 panelGrosor     | Col 13 panelTipo       | Col 14 base (tipo tablero)
Col 15 acabado         | Col 16 suministro      | Col 17 perfilado
Col 18 colorPanel      | Col 19 colorEstructura | Col 20 colorCarpinteria
Col 21 extra (notas)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUES DXF EN LA PLANTILLA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pilares estándar:      PL - pilar 2300 / 2400 / 2440
Pilares con panel:     PILAR PANEL {G} ANCHO {A}  donde G=50/60/80/100, A=2350/2400/2440
Cajetín atributos:     CAJETIN_VALS (atribs: OB, RAL, NS, SUMINISTRO, FECHA, OFERTA)
Bloques cubierta:      pendiente de identificar en plantilla
Bloques paneles:       pendiente de identificar en plantilla

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAPAS DXF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PL-LIM-CASETA    contorno módulo
PL-PILARES       bloques de pilares
CORREAS          líneas de correas en planta (color 4 cian) + sección carril derecha
CARRIL           carriles (color 8 gris, línea continua)
Cotas            dimensiones nativas DXF + rect redondeado Perfil Base + tablero amarillo
0                entidades generales
ALZ-EST-BA-DIB   rectángulo verde del alzado de base (hbase × L)
ALZ-CER-DIB      rectángulos de correas en el alzado (120×100mm, uno por correa)
Ejes             líneas verticales de eje de correas dentro del módulo (color 8)
TEXTO            textos de muñones, pilares, distribución correas, tipo+acabado, serie
SOMBRAS          hatch sólido verde (color 3) representación tablero dentro del módulo
CUADROS          franjas y rótulos de la sección del carril (zona derecha)
PL-CER-DIB       detalle constructivo sección carril (zona derecha del módulo)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIMSTYLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PMP-T-50   cotas entre correas (escala 50)
PMP-T-60   cotas totales largo y ancho (escala 60)
PMP-T-75   base de referencia para crear los anteriores

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OFFSETS CARRIL VERTICAL (medidos del ala interior del bloque de pilar, rot=180)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A=2350 -> 170mm  |  A=2400 -> 195mm  |  A=2440 -> 215mm
(independiente del grosor de panel - solo depende del ancho del módulo)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GROSORES DE PANEL -> CARRIL Y PILAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
panel <= 40mm  -> carril 40mm, pilar estándar (PL - pilar)
panel <= 50mm  -> carril 50mm, PILAR PANEL 50
panel <= 70mm  -> carril 60mm, PILAR PANEL 60
panel <= 90mm  -> carril 80mm, PILAR PANEL 80
panel >  90mm  -> carril 100mm, PILAR PANEL 100
"""
import sys, os, csv, datetime

# Forzar UTF-8 en stdout para evitar errores en consolas Windows con cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import ezdxf
except ImportError:
    os.system("pip install ezdxf --break-system-packages -q")
    import ezdxf

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
# Rutas posibles de plantilla (se usa la primera que exista)
_RUTAS_PLANTILLA = [
    r"C:\Users\modulos6\OneDrive\AUTOCAD\PLANTILLA.dxf",
    r"S:\OneDrive\AUTOCAD\PLANTILLA.dxf",
    r"C:\Users\David\Desktop\AUTOCAD\PLANTILLA.dxf",
]
PLANTILLA_DXF = next((r for r in _RUTAS_PLANTILLA if os.path.isfile(r)), _RUTAS_PLANTILLA[0])
CARPETA_SALIDA = os.path.join(os.path.dirname(PLANTILLA_DXF), "Generados")
TECNICO        = "D.P.Y."

# Punto origen del módulo dentro del marco A3
MODULO_X0 = 373364.0
MODULO_Y0 = -117207.0

# Zona a limpiar (cubre los 3 módulos de ejemplo de la plantilla)
# Módulo original:  x≈367000-392000
# Módulo ACTUAL:    x≈406951-412951
# Módulo NUEVO:     x≈417923-423923
# Se amplía la zona para barrer todo ese rango de una vez
ZONA_X = (367000.0, 426000.0)
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
    """
    Altura del perfil de base según tabla ALTURA_PERFILES.
    HORMIGONADA devuelve string "UPN Xmm".
    Resto devuelve entero (mm).
    NOTA: "BASE AISLADA e40 / CARRIL > e50" significa panel > 50mm.
    Panel exactamente e50 usa carril e50 -> NO sube la base a 160.
    La condición es p > 50 (no >= 50).
    """
    try: L=int(l); A=int(a); p=int(panel) if panel else 0
    except: return 137
    t = (base or "").strip().upper()
    # BASE HORMIGONADA (con UPN)
    if t == "HORMIGONADA": return "UPN 140" if L <= 7000 else "UPN 160"
    # BANDEJA TRAMEX
    if t == "TRAMEX":      return 200
    # SANEAMIENTO
    if t == "SANEAMIENTO": return 240
    # BASE TABLERO estándar (HIDRÓFUGO, FENÓLICO, etc.)
    v = 137 if L <= 6000 else 160 if L <= 8500 else 200
    # Panel > 50mm (carril > e50) -> mínimo 160
    if p > 50: v = max(v, 160)
    # Ancho > 2500mm -> mínimo 160
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
    # Módulo mini AIS WC MINI: A=1190, siempre panel 40, pilar especial 125x125
    if a <= 1190:
        return "PILAR PANEL 40 ANCHO 1190"
    ancho_bloque = 2400 if a==2400 else 2440 if a==2440 else 2350
    def _fallback():
        n = ancho_bloque if ancho_bloque in (2400,2440) else 2300
        return f"PL - pilar {n}"
    try:
        p = int(panel_grosor)
        if   p <= 40: return _fallback()
        elif p <= 50: g = 50
        elif p <= 70: g = 60
        elif p <= 90: g = 80
        else:         g = 100
        return f"PILAR PANEL {g} ANCHO {ancho_bloque}"
    except (ValueError, TypeError):
        return _fallback()

def calc_correas(L, base_str, A=None):
    # Módulo mini AIS WC MINI (A<=1190): correa única centrada en L/2
    # Cotas: 595 izq + 595 der = 1190mm
    # tablero=1220 para que la cota de tablero use el valor estándar Hidrófugo
    if A is not None and int(A) <= 1190:
        return [round(int(L) / 2)], 1220
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
        elif p <= 50: return 50
        elif p <= 70: return 60
        elif p <= 90: return 80
        else:         return 100
    except (ValueError, TypeError):
        return 40

# ─── LIMPIAR MÓDULO DE EJEMPLO ────────────────────────────────────────────────

def _en_zona(e):
    # Algunas entidades especiales (ARCALIGNEDTEXT, etc.) no tienen atributo layer
    try:
        _layer = e.dxf.layer
    except Exception:
        return False
    # Capas que se borran siempre (sin comprobar coordenadas)
    capas_borrar_siempre = {
        'PL-LIM-CASETA', 'PL-PILARES', 'PL-PIL-DIB', 'CORREAS', 'CARRIL',
        'ALZ-EST-BA-DIB', 'ALZ-CER-DIB', 'Ejes', 'SOMBRAS',
        'PL-CER-DIB', 'CUADROS',
    }
    if _layer in capas_borrar_siempre:
        return True
    # Capas que solo se borran si están dentro de la zona de los módulos de ejemplo
    if _layer in ('0', 'Cotas', 'TEXTO', 'Estructura LF'):
        t = e.dxftype()
        pts = []
        if t == 'LINE':        pts = [(e.dxf.start.x, e.dxf.start.y)]
        elif t == 'LWPOLYLINE':
            p = list(e.get_points())
            pts = [(p[0][0], p[0][1])] if p else []
        elif t in ('MTEXT','TEXT'): pts = [(e.dxf.insert.x, e.dxf.insert.y)]
        elif t == 'INSERT':    pts = [(e.dxf.insert.x, e.dxf.insert.y)]
        elif t == 'DIMENSION':
            try: pts = [(e.dxf.defpoint.x, e.dxf.defpoint.y)]
            except: pass
        elif t == 'HATCH':
            # Para HATCH buscar un punto representativo via bounding box de paths
            try:
                for path in e.paths.paths:
                    if hasattr(path, 'vertices') and path.vertices:
                        pts = [(path.vertices[0][0], path.vertices[0][1])]
                        break
                    elif hasattr(path, 'edges') and path.edges:
                        edge = path.edges[0]
                        if hasattr(edge, 'start'):
                            pts = [(edge.start[0], edge.start[1])]
                        elif hasattr(edge, 'center'):
                            pts = [(edge.center[0], edge.center[1])]
                        break
            except: pass
        elif t == 'CIRCLE':
            pts = [(e.dxf.center.x, e.dxf.center.y)]
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
    # El bloque PILAR PANEL 40 ANCHO 1190 tiene punto de inserción en la esquina
    # interior del módulo (x negativo, y positivo en coords locales) ->
    # orientaciones diferentes a los bloques estándar.
    if nombre_bloque == 'PILAR PANEL 40 ANCHO 1190':
        # Bloque: (0,0)=esquina inf-der, geometría hacia izq+arriba
        # Para que cada pilar apunte al interior del módulo:
        esquinas = [(x0,y0,0,-1),(x1,y0,0,1),(x0,y1,180,1),(x1,y1,180,-1)]
    else:
        esquinas = [(x0,y0,180,1),(x1,y0,180,-1),(x0,y1,0,-1),(x1,y1,0,1)]
    for ix, iy, rot, xs in esquinas:
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
# offset Y carril vertical: depende del ancho del módulo (ala interior del pilar)
# Para módulo mini 1190 (pilar 125x125): offset = 125 en todas las direcciones
CARRIL_OFS_V_Y_MAP  = {2350: 170, 2400: 195, 2440: 215}
CARRIL_OFS_H_X_MAP  = {1190: 90}    # override de H_X para módulo mini 1190 (ala interior pilar 125x125 = 90mm)
CARRIL_OFS_V_Y_MINI = 90             # offset V_Y para módulo mini 1190 (ala interior = 90mm)

def dibujar_carriles(msp, x0, y0, x1, y1, grosor, ancho_modulo=2350):
    """
    Dibuja los 4 carriles (2 horizontales + 2 verticales) en capa CARRIL.
    grosor: grosor del carril en mm (= grosor del panel, mín 40)
    Para pilar 125x125 (módulo mini 1190): los carriles llegan hasta el ala del pilar (125mm).
    """
    A = ancho_modulo

    # Offset horizontal: por defecto 142, para mini 1190 = 125 (topa con pilar 125x125)
    ofs_h_x = CARRIL_OFS_H_X_MAP.get(A, CARRIL_OFS_H_X)
    cx_ini = x0 + ofs_h_x
    cx_fin = x1 - ofs_h_x

    for cy_base in [y0 + CARRIL_OFS_H_Y, y1 - CARRIL_OFS_H_Y - grosor]:
        msp.add_lwpolyline(
            [(cx_ini, cy_base),(cx_fin, cy_base),(cx_fin, cy_base+grosor),(cx_ini, cy_base+grosor)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})

    # Offset vertical: mapeado por ancho, para mini 1190 = 125
    ofs_v_y = CARRIL_OFS_V_Y_MINI if A <= 1190 else CARRIL_OFS_V_Y_MAP.get(A, 170)
    cy_ini = y0 + ofs_v_y
    cy_fin = y1 - ofs_v_y

    for cx_base in [x0 + CARRIL_OFS_V_X, x1 - CARRIL_OFS_V_X - grosor]:
        msp.add_lwpolyline(
            [(cx_base, cy_ini),(cx_base+grosor, cy_ini),(cx_base+grosor, cy_fin),(cx_base, cy_fin)],
            close=True, dxfattribs={'layer':'CARRIL', 'color':8})

    print(f"  Carriles: grosor={grosor}mm  ofs_h_x={ofs_h_x}  ofs_v_y={ofs_v_y}")

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

# NOTA: rellenar_cajetin eliminada - ahora se usa add_auto_attribs directamente

def _munon_pilar_str(A, long_pilar, panel_grosor=0):
    """Devuelve (texto_munon, texto_pilar) según ancho módulo, longitud de pilar y grosor panel."""
    # Dimensiones según ancho A: exterior del pilar
    # Valores estándar: A=2350 -> 195x167, A=2400 -> 220x192, A=2440 -> 220x192
    p = int(panel_grosor) if panel_grosor else 0
    if A <= 1190:       px, py = 125, 125   # módulo mini AIS WC MINI
    elif p > 90:        px, py = 245, 217   # panel grueso -> pilar especial
    elif A <= 2350:     px, py = 195, 167
    elif A == 2400:     px, py = 220, 167
    elif A == 2440:     px, py = 240, 167
    else:               px, py = 220, 167
    # Muñón = pilar - 20mm en ambas dimensiones
    mx, my = px - 20, py - 20
    return (f"MUÑONES {mx}x{my}mm.", f"PILARES {px}x{py}x{long_pilar}mm")

def _rect_redondeado(msp, x_ini, y_bot, x_fin, y_top, radio, layer, color):
    """
    Dibuja un rectángulo con esquinas redondeadas usando LWPOLYLINE con bulge.
    bulge = tan(angulo/4) -> para 90° = tan(22.5°) ≈ 0.414
    """
    b = 0.414  # cuarto de círculo
    r = radio
    # Los puntos van en sentido antihorario:
    # Empezando en esquina superior izquierda, siguiendo sentido horario con bulge negativo
    pts = [
        (x_ini + r, y_top,  -b),   # top-left arc start
        (x_fin - r, y_top,   0.0), # top-right arc start
        (x_fin,     y_top - r, -b),
        (x_fin,     y_bot + r, 0.0),
        (x_fin - r, y_bot,   -b),
        (x_ini + r, y_bot,   0.0),
        (x_ini,     y_bot + r, -b),
        (x_ini,     y_top - r, 0.0),
    ]
    msp.add_lwpolyline(
        [(p[0], p[1], 0, 0, p[2]) for p in pts],
        format='xyseb', close=True,
        dxfattribs={'layer': layer, 'color': color})

def _hatch_rect_redondeado(msp, cx, dy_top, dy_bot, semiancho, radio, color_hatch, layer_hatch):
    """Dibuja un HATCH sólido en un rect redondeado usando EdgePath."""
    import math
    hatch = msp.add_hatch(dxfattribs={'layer': layer_hatch, 'color': color_hatch})
    hatch.set_solid_fill(color=color_hatch)
    ep = hatch.paths.add_edge_path()

    x0h = cx - semiancho
    x1h = cx + semiancho
    r = radio
    yb = dy_bot
    yt = dy_top

    # Arcos y líneas en sentido antihorario (exterior)
    # Igual que la LWPOLYLINE pero en formato EdgePath
    # Esquina sup-izq: arc centro (x0h+r, yt-r), 90°->180°
    ep.add_arc(center=(x0h + r, yt - r), radius=r, start_angle=90,  end_angle=180, ccw=True)
    # Lado izquierdo: de (x0h, yt-r) a (x0h, yb+r)
    ep.add_line(start=(x0h, yt - r), end=(x0h, yb + r))
    # Esquina inf-izq: arc centro (x0h+r, yb+r), 180°->270°
    ep.add_arc(center=(x0h + r, yb + r), radius=r, start_angle=180, end_angle=270, ccw=True)
    # Lado inferior: de (x0h+r, yb) a (x1h-r, yb)
    ep.add_line(start=(x0h + r, yb), end=(x1h - r, yb))
    # Esquina inf-dcha: arc centro (x1h-r, yb+r), 270°->360°
    ep.add_arc(center=(x1h - r, yb + r), radius=r, start_angle=270, end_angle=360, ccw=True)
    # Lado derecho: de (x1h, yb+r) a (x1h, yt-r)
    ep.add_line(start=(x1h, yb + r), end=(x1h, yt - r))
    # Esquina sup-dcha: arc centro (x1h-r, yt-r), 0°->90°
    ep.add_arc(center=(x1h - r, yt - r), radius=r, start_angle=0, end_angle=90, ccw=True)
    # Lado superior: de (x1h-r, yt) a (x0h+r, yt)
    ep.add_line(start=(x1h - r, yt), end=(x0h + r, yt))

# ─── OFFSETS DEL ALZADO BASE (medidos del módulo NUEVO en PLANTILLA.dxf) ───────

_ALZ_RECT_OFS_BOT = 1186.0  # y1 → borde inferior rect ALZ-EST-BA-DIB
# (borde superior = _ALZ_RECT_OFS_BOT + hbase)

# Rectángulo redondeado "PERFIL BASE" (pegado al borde derecho, ancho fijo 1038mm)
_PRB_DX_ANCHO = 1038.0      # ancho del rect redondeado PERFIL BASE
_PRB_DY_BOT   = 803.0       # y1 + 803 = borde inferior
_PRB_DY_TOP   = 1015.0      # y1 + 1015 = borde superior

# Texto "PERFIL BASE Xmm" dentro del rectángulo
_PRB_TXT_DX   = 5028.0      # desde x0
_PRB_TXT_DY   = 880.0       # desde y1

# Cajas MUÑONES y PILARES (LWPOLYLINE color=5 azul)
_CAJA_MUN_DX0 = 1718.0;  _CAJA_MUN_DX1 = 3032.0
_CAJA_PIL_DX0 = 3149.0;  _CAJA_PIL_DX1 = 4615.0
_CAJA_DY_BOT  = 1681.0;  _CAJA_DY_TOP  = 1865.0

# Textos encima del alzado (posiciones relativas a x0 y y1)
_TXT_MUN_DX   = 1758.0;  _TXT_MUN_DY  = 1741.0
_TXT_PIL_DX   = 3189.0;  _TXT_PIL_DY  = 1741.0
_TXT_CHK1_DX  = 1616.0;  _TXT_CHK1_DY = 2349.0
_TXT_CHK2_DX  = 1616.0;  _TXT_CHK2_DY = 2093.0
_TXT_DIST_DX  = 1744.0;  _TXT_DIST_DY = 2807.0

# Cotas encima entre correas: dy_defpoint desde y1
_COTA_COR_DY  = 270.0

# Cota vertical hbase: a la izquierda del módulo
_COTA_HBASE_DX = -218.0     # desde x0

# Tablero (HATCH + contorno amarillo) centrado en módulo
_TAB_DX_SEMI  = 480.0       # semiancho del rect de tablero
_TAB_DY_TOP   = -843.7      # desde y1 (negativo = dentro del módulo)
_TAB_DY_BOT   = -1118.2
_TAB_R        = 50.0        # radio arcos esquinas
_TAB_TXT_DX   = 1365.0      # texto tablero a la derecha: desde x1
_TAB_TXT_DY   = -1454.0     # desde y1

def dibujar_alzado_base(msp, doc, x0, y0, x1, y1, hbase, correas, tipo_tablero, long_pilar, A, g_carril):
    """
    Dibuja la información encima del módulo:
    - Rectángulo verde ALZ-EST-BA-DIB (largo módulo x hbase)
    - Rectángulos de correas ALZ-CER-DIB (120x100 en cada eje de correa)
    - Líneas de eje verticales (Ejes) en cada correa
    - Cotas PMP-T-60 entre correas (encima del módulo)
    - Cota vertical PMP-T-75 del hbase
    - Rectángulo redondeado PERFIL BASE con texto
    - Cajas MUÑONES y PILARES con textos
    - Textos fijos de comprobación
    - Tablero (HATCH + contorno amarillo) centrado en módulo
    """
    L = float(x1 - x0)

    # ── A. Rectángulo verde (ALZ-EST-BA-DIB) ──────────────────────────────────
    alz_y0 = y1 + _ALZ_RECT_OFS_BOT
    alz_y1 = alz_y0 + hbase
    for p1, p2 in [
        ((x0, alz_y0), (x0, alz_y1)),
        ((x0, alz_y1), (x1, alz_y1)),
        ((x1, alz_y1), (x1, alz_y0)),
        ((x1, alz_y0), (x0, alz_y0)),
    ]:
        msp.add_line(p1, p2, dxfattribs={'layer': 'ALZ-EST-BA-DIB'})

    # ── B. Correas en alzado → bloque CORREA BASE ────────────────────────────
    # El bloque CORREA BASE tiene punto de inserción en el borde SUPERIOR (y=0 local).
    # Offset medido en la plantilla: y1 + 1318.28mm = insert_y del bloque.
    _ALZ_CER_INSERT_OFS = 1318.28
    alz_cer_insert_y = y1 + _ALZ_CER_INSERT_OFS
    for pos in correas:
        cx_correa = x0 + pos
        msp.add_blockref('CORREA BASE', insert=(cx_correa, alz_cer_insert_y),
                         dxfattribs={'layer': 'ALZ-CER-DIB'})

    # ── C. Ejes eliminados: se superponen con las líneas CORREAS cian del módulo

    # ── D eliminada: cotas entre correas van ABAJO del módulo (en generar_modulo)

    # ── E. Cota vertical hbase a la izquierda (PMP-T-75) ──────────────────────
    cota_v(msp, doc, x0, alz_y0, x0, alz_y1,
           x0 + _COTA_HBASE_DX, 'PMP-T-75')

    # ── F-I eliminados: PERFIL BASE, MUÑONES/PILARES, textos y tablero
    # Ahora se gestionan mediante bloques de la plantilla en dibujar_bloques_recuadros


# ─── ZONA DERECHA (sección carril + tablero) ──────────────────────────────────
#
# Todos los offsets son fijos respecto a x1 e y0/y1 del módulo.
# Medidos del ejemplo de plantilla (módulo 6000x2350 panel 40mm)

def dibujar_zona_derecha(msp, x0, y0, x1, y1, g_carril, A):
    """
    Dibuja a la derecha del módulo:
    - Sección del carril vertical (PL-CER-DIB + CUADROS + CORREAS) - geometría fija
    - Rectángulo del tablero (color amarillo) con texto 'Aglomerado HidrófugoX mm'
    - Círculo y líneas de referencia
    """
    # ── Geometría fija de la sección del carril ────────────────────────────────
    # Referencia: módulo 6000x2350, panel 40mm, carril 40mm
    # PL-CER-DIB superior (en borde top del módulo)
    def _add_poly(pts, layer, color=256):
        msp.add_lwpolyline(pts, close=True,
                           dxfattribs={'layer': layer, 'color': color})

    def _add_line(p1, p2, layer, color=256):
        msp.add_line(p1, p2, dxfattribs={'layer': layer, 'color': color})

    # Offsets desde x1 e y1 para el bloque de sección de carril
    # Todos medidos de la plantilla
    dx_cua  = 270   # CUADROS: borde izq desde x1
    dx_cua2 = 289   # CUADROS: borde der (= PL-CER-DIB borde izq)
    dx_cor1 = 291   # CORREAS: inicio
    dx_cor2 = 393   # CORREAS: fin (= ancho carril 102mm para panel 40mm)
    dx_plc1 = 289   # PL-CER-DIB: borde izq
    dx_plc2 = 429   # PL-CER-DIB: borde der

    # Ajuste de dx_cor2 según grosor de carril real (base 102mm para 40mm)
    # La sección del carril tiene ancho = g_carril + 62 (alas del pilar ~31mm c/u)
    dx_cor2 = dx_cor1 + g_carril + 62

    # Altura de la sección (igual al alto del módulo)
    h_mod = float(y1 - y0)   # = A

    # ── CUADROS (línea delgada vertical, borde izq) ────────────────────────────
    _add_poly([(x1+dx_cua,  y0-20), (x1+dx_cua2, y0-20),
               (x1+dx_cua2, y1+20), (x1+dx_cua,  y1+20)],
              layer='CUADROS')

    # ── CORREAS (sección del carril, relleno) ─────────────────────────────────
    ofs_y_cor = 82   # offset desde borde del módulo al inicio del área del carril
    _add_poly([(x1+dx_cor1, y0+ofs_y_cor), (x1+dx_cor2, y0+ofs_y_cor),
               (x1+dx_cor2, y1-ofs_y_cor), (x1+dx_cor1, y1-ofs_y_cor)],
              layer='CORREAS')

    # ── PL-CER-DIB superior (esquina top del módulo) ──────────────────────────
    dy_plc_h   = 105   # alto del rect PL-CER-DIB
    dy_plc_ofs =  84   # offset desde borde al tramo de líneas
    for cy_base, sign in [(y1, -1), (y0, +1)]:
        # Rectángulo exterior doble
        _add_poly([(x1+dx_plc1, cy_base + sign*0),
                   (x1+dx_plc2, cy_base + sign*0),
                   (x1+dx_plc2, cy_base + sign*dy_plc_h),
                   (x1+dx_plc1, cy_base + sign*dy_plc_h)],
                  layer='PL-CER-DIB')
        _add_poly([(x1+dx_plc1+2, cy_base + sign*2),
                   (x1+dx_plc2-2, cy_base + sign*2),
                   (x1+dx_plc2-2, cy_base + sign*(dy_plc_h-2)),
                   (x1+dx_plc1+2, cy_base + sign*(dy_plc_h-2))],
                  layer='PL-CER-DIB')
        # Líneas de detalle interior
        xr = x1 + dx_plc2
        xl = x1 + dx_plc1 + (dx_plc2-dx_plc1) - 34
        _add_line((xr, cy_base + sign*0),   (xr, cy_base + sign*dy_plc_ofs),   'PL-CER-DIB')
        _add_line((xr-2, cy_base + sign*2), (xr-2, cy_base + sign*(dy_plc_ofs-2)), 'PL-CER-DIB')
        _add_line((xl, cy_base + sign*dy_plc_ofs),   (xr, cy_base + sign*dy_plc_ofs),   'PL-CER-DIB')
        _add_line((xl-2, cy_base + sign*(dy_plc_ofs-2)), (xr-2, cy_base + sign*(dy_plc_ofs-2)), 'PL-CER-DIB')
        _add_line((xl, cy_base + sign*dy_plc_ofs),   (xl, cy_base + sign*dy_plc_h),   'PL-CER-DIB')
        _add_line((xl-2, cy_base + sign*(dy_plc_ofs-2)), (xl-2, cy_base + sign*(dy_plc_h-2)), 'PL-CER-DIB')
        _add_line((xl-2, cy_base + sign*(dy_plc_h-2)), (xl, cy_base + sign*(dy_plc_h-2)), 'PL-CER-DIB')

    # ── Detalle panel (PL-CER-DIB) alejado + corte ────────────────────────────
    dx_det = 981   # borde izq del detalle
    det_w  = 210
    det_h  = 280
    det_y  = y0   # se ancla en el borde inferior del módulo
    _add_poly([(x1+dx_det,       det_y - det_h),
               (x1+dx_det+det_w, det_y - det_h),
               (x1+dx_det+det_w, det_y - 0),
               (x1+dx_det,       det_y - 0)],
              layer='PL-CER-DIB')
    _add_poly([(x1+dx_det+4,       det_y - 4),
               (x1+dx_det+det_w-4, det_y - 4),
               (x1+dx_det+det_w-4, det_y - det_h+4),
               (x1+dx_det+4,       det_y - det_h+4)],
              layer='PL-CER-DIB')
    for p1, p2 in [
        ((x1+dx_det+det_w,   det_y),       (x1+dx_det+det_w-42, det_y)),
        ((x1+dx_det+det_w-4, det_y-4),     (x1+dx_det+det_w-46, det_y-4)),
        ((x1+dx_det+det_w-42, det_y),      (x1+dx_det+det_w-42, det_y-68)),
        ((x1+dx_det+det_w-46, det_y-4),    (x1+dx_det+det_w-46, det_y-64)),
        ((x1+dx_det,         det_y-68),    (x1+dx_det+det_w-42, det_y-68)),
        ((x1+dx_det,         det_y-64),    (x1+dx_det+det_w-46, det_y-64)),
        ((x1+dx_det,         det_y-68),    (x1+dx_det,          det_y-64)),
        ((x1+dx_det,         det_y-det_h+4), (x1+dx_det,        det_y-det_h)),
    ]:
        _add_line(p1, p2, 'PL-CER-DIB')

    # ── CORREAS detalle panel ──────────────────────────────────────────────────
    dx_cor_det  = 675
    cor_det_w   = 349
    cor_det_h   = 204
    cor_det_y1  = det_y - 4          # tope superior
    cor_det_y0  = cor_det_y1 - cor_det_h
    _add_poly([(x1+dx_cor_det,          cor_det_y0),
               (x1+dx_cor_det+cor_det_w, cor_det_y0),
               (x1+dx_cor_det+cor_det_w, cor_det_y1),
               (x1+dx_cor_det,           cor_det_y1)],
              layer='CORREAS')

    # ── CUADROS rótulo inferior detalle ───────────────────────────────────────
    cu_w = 372; cu_h = 33
    cu_y = cor_det_y0
    _add_poly([(x1+658, cu_y-cu_h), (x1+658+cu_w, cu_y-cu_h),
               (x1+658+cu_w, cu_y), (x1+658, cu_y)],
              layer='CUADROS')

    # ── Círculo de referencia + líneas ────────────────────────────────────────
    circ_cx = x1 + 371
    circ_cy = y0 + 59          # dy_top=-2291 -> y1-2291 = y0+A-2291 = y0+59 para A=2350
    msp.add_circle((circ_cx, circ_cy), radius=130,
                   dxfattribs={'layer': 'Cotas'})
    # Líneas de referencia
    _add_line((x1+289, y1-105), (x1+291, y1-105), 'Cotas')
    _add_line((x1+632, y0+204), (x1+797, y0+373), 'Cotas')
    _add_line((x1+874, y0+326), (x1+965, y0+568), 'Cotas')

    # ── Texto tablero a la derecha (tipo y grosor) ─────────────────────────────
    # El grosor del tablero: Hidrófugo=19mm, Fenólico=18mm
    # (lo determinamos a partir de g_carril pero se pasa por arg externo, aquí fijo)
    # Se dibujará desde dibujar_textos_modulo con acceso al tipo


# ─── TEXTOS DENTRO DEL MÓDULO ─────────────────────────────────────────────────

def dibujar_textos_modulo(msp, x0, y0, x1, y1, base, acabado, serie):
    """
    Dibuja dentro del módulo (centrado en X):
    - Tipo tablero + acabado  (dy_bot=994)
    - Serie                   (dy_bot=1369)
    Y a la derecha del módulo:
    - Texto 'Aglomerado\\nHidrófugo/Fenólico Xmm'
    """
    cx = (x0 + x1) / 2.0
    A  = float(y1 - y0)

    # Tipo de tablero y grosor
    _b = (base or '').strip().upper()
    es_fenolico = 'FENOL' in _b.replace('Ó','O').replace('É','E').replace('Í','I')
    tipo_txt  = 'Fenólico' if es_fenolico else 'Hidrófugo'
    grosor_t  = 18 if es_fenolico else 19

    # Texto "TIPO + ACABADO" centrado
    linea1 = f'{tipo_txt.upper()} + {(acabado or "").strip().upper()}'
    msp.add_mtext(linea1, dxfattribs={
        'layer': 'TEXTO',
        'char_height': 112.5,
        'insert': (cx, y0 + 994),
        'attachment_point': 5,  # Middle center
    })

    # Texto serie centrado
    if serie:
        serie_txt = serie.strip().replace(',', ' - ')
        msp.add_mtext(serie_txt, dxfattribs={
            'layer': 'TEXTO',
            'char_height': 112.5,
            'insert': (cx, y0 + 1369),
            'attachment_point': 5,
        })

    # Texto tablero a la derecha
    txt_tab = f'Aglomerado\\P{tipo_txt} {grosor_t}mm'
    msp.add_mtext(txt_tab, dxfattribs={
        'layer': 'TEXTO',
        'char_height': 75.0,
        'width': 927.0,
        'insert': (x1 + _TAB_TXT_DX, y1 + _TAB_TXT_DY),
        'attachment_point': 5,
    })



# ─── BLOQUES RECUADROS (nuevos en la plantilla corregida) ─────────────────────
#
# Bloques disponibles en la PLANTILLA.dxf:
#   'RECUADRO H PERFIL BASE Xmm'
#       insert=(x1, y1+909.5)  bbox local: x=-1037.7 a 0  y=-106.3 a +106.3
#       Texto MTEXT interior con valor "Xmm" (se actualiza mediante ATTDEF o texto directo)
#
#   'RECUADROS MEDIDAS PILARES - MUÑONES'
#       insert=(cx_mod, y1+1784.3)  bbox local: x=-1431.5 a 1466  y=-183.4 a 0
#       Textos: " MUÑONES 175x147mm." y "PILARES 195x167x2525mm"
#       (se regeneran dinámicamente → el bloque se inserta y sus ATTDEFs se sobreescriben)
#
#   'RECUADRO TÍTULO PLANO'
#       insert=(cx_mod, y1+3009.6)  bbox local: x=-1625 a 1677  y=-421 a 0
#       Texto: "DISTRIBUCIÓN CORREAS BASE C/ HIDRÓFUGO|FENÓLICO"
#
#   'RECUADRO NÚMERO DE UD (MÓDULOS) NUMERO SERIE'
#       insert=(x1+714.2, y1+2671.6)  bbox local: centrado ±689/±218
#       Texto MTEXT: "X UNIDADES"
#
#   'CARRIL PARA PANEL DE Xmm'
#       insert=(x1+477.4, y1+370.5)
#       Texto MTEXT: "CARRIL PARA PANEL DE Xmm"
#
#   'CORTE CARRIL CARA LARGA'  (2 inserts enfrentados a la derecha del módulo)
#       SOLO cuando el módulo es ADOSADO (los carriles interiores no llevan panel,
#       hay que taparlos con tablero hidrófugo/fenólico).
#       rot=0   insert=(x1+429, y0)   → corte inferior
#       rot=180 insert=(x1+429, y1)   → corte superior (espejado)
#       De momento se insertan siempre; en el futuro condicionarlo al tipo de suministro.
#
#   'RECUADRO TABLERO Y SUELO'
#       insert=(cx_mod, y1-1373.3)  → dentro del módulo, a ≈ 1/3 desde arriba
#       Texto MTEXT: "HIDRÓFUGO + ACABADO" o "FENÓLICO + ACABADO"
#
# NOTA: los bloques con textos variables (pilares, muñones, carril, tablero, título)
# se insertan primero y luego se sobrescriben sus textos en el MTEXT del bloque
# encontrado en el modelspace (por posición). Por ahora se insertan directamente
# con el texto ya incrustado en la definición del bloque (estático); cuando haga
# falta actualizar el texto, habrá que explotar el bloque o usar ATTDEF.

def _attribs(blk_ref, vals, doc=None):
    """
    Rellena los ATTRIBs de un INSERT con el dict {tag: valor}.
    Solo aplica align_point cuando halign requiere dos puntos (3=ALIGNED, 4=MIDDLE, 5=FIT).
    Para halign 0/1/2 (LEFT/CENTER/RIGHT) no se toca align_point.
    """
    try:
        blk_ref.add_auto_attribs(vals)
        blk_ref.attribs_follow = True  # flag HAS_ATTRIB: AutoCAD necesita esto para renderizar attribs
        # Forzar valign=0 (BASELINE) en todos los ATTRIBs para que coincidan
        # con los TEXTs fijos del bloque que usan valign=0 por defecto en AutoCAD
        for _a in blk_ref.attribs:
            _a.dxf.valign = 0
        if doc is not None:
            blk_name = blk_ref.dxf.name
            blk_def = doc.blocks.get(blk_name)
            if blk_def:
                attdef_map = {}
                for e in blk_def:
                    if e.dxftype() == 'ATTDEF':
                        attdef_map[e.dxf.tag] = e
                ix, iy = blk_ref.dxf.insert.x, blk_ref.dxf.insert.y
                for attrib in blk_ref.attribs:
                    tag = attrib.dxf.tag
                    if tag not in attdef_map:
                        continue
                    attdef = attdef_map[tag]
                    halign = getattr(attdef.dxf, 'halign', 0)
                    # Solo para justificaciones que usan dos puntos
                    if halign in (3, 4, 5):
                        try:
                            ap = attdef.dxf.align_point
                            attrib.dxf.align_point = (ix + ap.x, iy + ap.y)
                        except Exception:
                            pass
                    else:
                        # Eliminar align_point si existe (no debe interferir)
                        try:
                            del attrib.dxf.align_point
                        except Exception:
                            pass

    except Exception:
        pass


def dibujar_bloques_recuadros(msp, doc, x0, y0, x1, y1, hbase, long_pilar, A,
                               panel_grosor, g_carril, panel_tipo, serie,
                               suministro, tipo_tablero, acabado):
    """
    Inserta los bloques de recuadros y rellena sus ATTRIBs dinámicos.
    """
    cx = (x0 + x1) / 2.0

    # Calcular dimensiones de muñones y pilares
    str_mun, str_pil = _munon_pilar_str(A, long_pilar, panel_grosor)
    # str_mun = "MUÑONES 175x147mm."  str_pil = "PILARES 195x167x2525mm"
    # Extraer solo las dimensiones (sin la etiqueta fija del bloque)
    mun_val = str_mun.replace('MUÑONES ', '').strip()   # "175x147mm."
    pil_val = str_pil.replace('PILARES ', '').strip()   # "195x167x2525mm"

    # Texto tablero: base del módulo (HIDRÓFUGO/FENÓLICO/HORMIGONADA)
    tablero_val = tipo_tablero.upper()  # "HIDRÓFUGO" o "FENÓLICO"

    # Texto tablero+suelo: base + acabado
    acabado_str = (acabado or '').strip()
    tablero_suelo_val = f"{tablero_val} + {acabado_str}" if acabado_str else tablero_val

    # Número de unidades (viene del campo serie: "35559-35562" → 4 uds)
    # El campo serie no da el número de unidades directamente.
    # Por ahora se deja vacío; se puede añadir un campo específico en el futuro.
    # El tag es '4UNIDADES_1UNIDAD' → el valor completo lo ponemos nosotros
    # Contamos rangos en la serie: "35559-35562" → 35562-35559+1 = 4
    try:
        partes = (serie or '').replace(' ','').split('-')
        if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            n_uds = int(partes[1]) - int(partes[0]) + 1
        elif len(partes) >= 3:
            # Formato "35559-35560-35561" → contar partes
            n_uds = len(partes)
        else:
            n_uds = 1
    except Exception:
        n_uds = 1
    uds_val = f"{n_uds} UNIDADES" if n_uds != 1 else "1 UNIDAD"

    # 1. RECUADRO H PERFIL BASE Xmm
    ref = msp.add_blockref('RECUADRO H PERFIL BASE Xmm',
                           insert=(x1, y1 + 909.5),
                           dxfattribs={'layer': 'Cotas'})
    _attribs(ref, {'HBASE': str(hbase)}, doc)

    # 2. RECUADROS MEDIDAS PILARES - MUÑONES
    ref = msp.add_blockref('RECUADROS MEDIDAS PILARES - MUÑONES',
                           insert=(cx, y1 + 1784.3),
                           dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'MUÑONES': mun_val, 'PILARES': pil_val}, doc)

    # 3. RECUADRO TÍTULO PLANO
    ref = msp.add_blockref('RECUADRO TÍTULO PLANO',
                           insert=(cx, y1 + 3009.6),
                           dxfattribs={'layer': 'Cotas'})
    _attribs(ref, {'TABLERO': tablero_val}, doc)

    # Textos *COMPROBAR debajo del título: centrados en el módulo
    from ezdxf.enums import TextEntityAlignment
    for dy, txt in [
        (2349.0, '*COMPROBAR LA MEDIDA DEL TABLERO ANTES DE SOLDAR'),
        (2093.0, '*COMPROBAR LAS DIMENSIONES DE LOS MUÑONES CON LOS PILARES'),
    ]:
        t_ent = msp.add_text(txt, dxfattribs={'layer': 'TEXTO', 'height': 82.9})
        t_ent.set_placement((cx, y1 + dy), align=TextEntityAlignment.CENTER)

    # 4. RECUADRO NÚMERO DE UD (MÓDULOS) NUMERO SERIE
    # 5. CARRIL PARA PANEL DE Xmm
    # Estos bloques van a la derecha del módulo - para módulos mini (A<=1190)
    # quedan fuera del marco, así que se omiten.
    if A > 1190:
        ref = msp.add_blockref('RECUADRO NÚMERO DE UD (MÓDULOS) NUMERO SERIE',
                               insert=(x1 + 714.2, y1 + 2671.6),
                               dxfattribs={'layer': 'Cotas'})
        _attribs(ref, {'4UNIDADES_1UNIDAD': uds_val}, doc)

        ref = msp.add_blockref('CARRIL PARA PANEL DE Xmm',
                               insert=(x1 + 477.4, y1 + 370.5),
                               dxfattribs={'layer': 'Cotas'})
        _attribs(ref, {'CARRIL': str(g_carril)}, doc)

    # 6. CORTE CARRIL CARA LARGA: solo para módulos normales (no mini AIS WC)
    if A > 1190:
        msp.add_blockref('CORTE CARRIL CARA LARGA',
                         insert=(x1 + 429.0, y0),
                         dxfattribs={'layer': 'PL-CER-DIB', 'rotation': 0})
        ref = msp.add_blockref('CORTE CARRIL CARA LARGA',
                               insert=(x1 + 429.0, y1),
                               dxfattribs={'layer': 'PL-CER-DIB', 'rotation': 180})
        ref.dxf.xscale = -1.0

    # 7. RECUADRO TABLERO Y SUELO
    ref = msp.add_blockref('RECUADRO TABLERO Y SUELO',
                           insert=(cx, y1 - 1373.3),
                           dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'TABLERO_SUELO': tablero_suelo_val}, doc)

    # 8. BLOQUE NÚMERO SERIE
    ref = msp.add_blockref('BLOQUE NÚMERO SERIE',
                           insert=(cx, y1 - 949.4),
                           dxfattribs={'layer': 'TEXTO'})
    _attribs(ref, {'SERIE': serie or '-'}, doc)


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
    hcub       = calc_hcubierta(L, A, base, panel, c("estCubierta"))
    # long_pilar: H del CSV es la altura INTERIOR del módulo (L, A, H = largo, ancho, H interior).
    # El pilar siempre mide H_interior + 25mm.
    # No depende de hbase ni hcub.
    # Ejemplos: H=2500 -> pilar=2525mm | H=2300 -> pilar=2325mm | H=3000 -> pilar=3025mm
    long_pilar = H + 25
    bloque_pil = nombre_bloque_pilar(A, panel)
    correas, tablero = calc_correas(L, base, A)
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
    MARGEN_X     = 1550.0   # margen horizontal (bloques derecha: Nº UD necesita x1+1404mm)
    MARGEN_Y_INF = 600.0    # margen debajo del módulo (cotas inferiores + holgura)
    MARGEN_Y_SUP = 450.0    # margen encima del último elemento

    # Espacio necesario encima del módulo:
    # _TXT_DIST_DY = 2807mm es la distancia del top del módulo al texto más alto
    # Elemento más alto: RECUADRO TÍTULO PLANO en y1+3009.6 -> necesita 3009.6 + margen
    _ESPACIO_ENCIMA = 3009.6 + MARGEN_Y_SUP   # 3009.6 + 450 = 3460mm

    # Tamaño mínimo del marco
    A3_W, A3_H = 7110.0, 5028.0
    w_min = max(float(L) + 2 * MARGEN_X, A3_W)
    # Alto mínimo: módulo + margen inferior + espacio encima
    h_min = max(float(A) + MARGEN_Y_INF + _ESPACIO_ENCIMA, A3_H)

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

    # ── CAJETIN_VALS: escalar y explotar ─────────────────────────────────────
    BLOQUE_W, BLOQUE_H = 7109.9, 5027.7
    sx = marco_w / BLOQUE_W
    sy = marco_h / BLOQUE_H

    # Rellenar valores en los ATTDEF del bloque
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

    from ezdxf.enums import TextEntityAlignment

    # Eliminar INSERT existente del modelspace
    for ent in list(msp):
        if ent.dxftype() == 'INSERT' and 'CAJET' in ent.dxf.name.upper():
            msp.delete_entity(ent)
            break

    # Explotar bloque: dibujar entidades escaladas directamente en modelspace
    for blk_ent in blk_def:
        t = blk_ent.dxftype()
        if t == 'LWPOLYLINE':
            pts = list(blk_ent.get_points(format='xyseb'))
            new_pts = [(MARCO_X0+p[0]*sx, MARCO_Y0+p[1]*sy, p[2], p[3], p[4]) for p in pts]
            msp.add_lwpolyline(
                new_pts, format='xyseb',
                close=True, dxfattribs={
                    'layer': blk_ent.dxf.layer,
                    'color': getattr(blk_ent.dxf,'color',256)})
        elif t == 'MTEXT':
            msp.add_mtext(blk_ent.text, dxfattribs={
                'insert': (MARCO_X0+blk_ent.dxf.insert.x*sx,
                           MARCO_Y0+blk_ent.dxf.insert.y*sy, 0),
                'char_height': blk_ent.dxf.char_height * min(sx,sy),
                'width':       blk_ent.dxf.width * sx,
                'attachment_point': blk_ent.dxf.attachment_point,
                'layer': blk_ent.dxf.layer,
                'color': getattr(blk_ent.dxf,'color',256)})
        elif t == 'ATTDEF':
            txt = msp.add_text(blk_ent.dxf.text, dxfattribs={
                'height': blk_ent.dxf.height * min(sx,sy),
                'layer':  blk_ent.dxf.layer,
                'style':  getattr(blk_ent.dxf,'style','Standard'),
                'color':  getattr(blk_ent.dxf,'color',256)})
            offset_y = blk_ent.dxf.height * 0.5
            txt.set_placement(
                (MARCO_X0+blk_ent.dxf.insert.x*sx,
                 MARCO_Y0+(blk_ent.dxf.insert.y+offset_y)*sy),
                align=TextEntityAlignment.MIDDLE_CENTER)

    print(f"  Cajetin OK: OB={_caj_vals['OB']!r} RAL={_caj_vals['RAL']!r} N/S={_caj_vals['NS']!r} FECHA={_caj_vals['FECHA']!r} OFERTA={_caj_vals['OFERTA']!r}")

    # Posicionar módulo: centrado horizontal, PEGADO AL FONDO del marco verticalmente
    # El alzado y textos se extienden hacia arriba, así que el módulo va abajo.
    AREA_CX = (MARCO_X0 + MARCO_X1) / 2.0
    x0 = AREA_CX - float(L) / 2.0
    y0 = MARCO_Y0 + MARGEN_Y_INF       # módulo pegado al fondo + margen inferior
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
    dibujar_carriles(msp, x0, y0, x1, y1, g_carril, A)

    # 7. Cotas con DIMENSION nativas
    # Nombre del tipo de tablero para la cota
    _base_upper = (base or '').strip().upper().replace('Ó','O').replace('É','E').replace('Í','I')
    tipo_tablero = 'Fenólico' if 'FENOL' in _base_upper else 'Hidrófugo'

    # Orden cotas encima del módulo (de abajo a arriba):
    #   1. Cota largo TOTAL       → OFS_TOT = 270mm sobre y1
    #   2. Cotas TABLERO 1220/1250 → OFS_TAB = 487mm sobre y1
    # Cotas entre CORREAS → van DEBAJO del módulo (junto a las de abajo)
    OFS_COR_BOT = 321   # cotas correas: debajo del módulo
    OFS_TOT     = 487   # cota largo total: encima de las de tablero
    OFS_TAB     = 270   # cotas tablero: más cerca del módulo, debajo de la total
    OFS_IZQ     = 321   # cota ancho: a la izquierda

    # Cotas entre correas → ABAJO del módulo (junto con y0)
    puntos_x = [x0] + [x0+pos for pos in correas] + [x1]
    for i in range(len(puntos_x)-1):
        xa, xb = puntos_x[i], puntos_x[i+1]
        cota_h(msp, doc, xa, y0, xb, y0, y0 - OFS_COR_BOT, 'PMP-T-50')

    # Cota largo total encima del módulo (PMP-T-60), más cerca
    cota_h(msp, doc, x0, y1, x1, y1, y1 + OFS_TOT, 'PMP-T-60')

    # Cotas de tablero encima, por encima de la cota total
    if correas:
        x_tab_ini     = x0 + CARRIL_OFS_V_X + g_carril + 5
        x_tab_fin_max = x1 - CARRIL_OFS_V_X - g_carril - 5
        x_tab = x_tab_ini
        while x_tab < x_tab_fin_max:
            fin = min(x_tab + tablero, x_tab_fin_max)
            cota_h(msp, doc, x_tab, y1, fin, y1, y1 + OFS_TAB, 'PMP-T-50', tipo_tablero)
            x_tab += tablero

    # Cota ancho izquierda (PMP-T-60)
    cota_v(msp, doc, x0, y0, x0, y1, x0 - OFS_IZQ, 'PMP-T-60')

    # ── 8. ELEMENTOS NUEVOS ──────────────────────────────────────────────────────

    hbase_draw = hbase if isinstance(hbase, int) else (140 if "140" in str(hbase) else 160)
    dibujar_alzado_base(msp, doc, x0, y0, x1, y1, hbase_draw, correas, tipo_tablero, long_pilar, A, g_carril)
    # dibujar_zona_derecha: ELIMINADO - los detalles de sección carril a la derecha
    # no forman parte del plano de estructura base estándar
    dibujar_bloques_recuadros(msp, doc, x0, y0, x1, y1, hbase_draw, long_pilar, A,
                              panel, g_carril, c("panelTipo"), c("serie"), c("suministro"),
                              tipo_tablero, c("acabado"))

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
        cliente  = _c(f0, 'cliente')
        if len(filas_g) == 1:
            f = filas_g[0]
            destino = _c(f, 'destino')
            base    = _c(f, 'base') or 'HIDRÓFUGO'
            grosor  = _c(f, 'panelGrosor') or '-'
            print(f"  [{i:>2}]  {numpedido:15}  {cliente:15}  {destino:15}  L={_c(f,'l')} A={_c(f,'a')}  {base:12}  {grosor}mm")
        else:
            print(f"  [{i:>2}]  {numpedido:15}  {cliente:15}  ({len(filas_g)} módulos)")
            for j, f in enumerate(filas_g, 1):
                destino = _c(f, 'destino')
                base    = _c(f, 'base') or 'HIDRÓFUGO'
                grosor  = _c(f, 'panelGrosor') or '-'
                notas   = _c(f, 'extra') or ''
                print(f"         M{j}  L={_c(f,'l')} A={_c(f,'a')}  {destino:15}  {base:12}  {grosor}mm  {notas}")
    print("─────────────────")

    while True:
        try:
            entrada = input("Número de pedido (0=todos, 1,2,3=varios): ").strip()
        except EOFError:
            continue
        if not entrada:
            continue
        try:
            nums = [int(x.strip()) for x in entrada.split(",")]
        except ValueError:
            continue
        if 0 in nums:
            return [f for _, filas_g in grupos for f in filas_g]
        if all(1 <= n <= len(grupos) for n in nums):
            result = []
            for n in nums:
                _, filas_g = grupos[n - 1]
                result.extend(filas_g)
            return result

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
    try:
        main()
    except Exception as _e:
        print(f"\nERROR: {_e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPulsa Enter para salir...")
