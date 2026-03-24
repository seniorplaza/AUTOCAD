"""
config.py — Constantes globales del proyecto de generación de planos DXF.
Rutas, columnas CSV, capas, colores, offsets de carriles y zonas de limpieza.
"""
import os

# ─── RUTAS ────────────────────────────────────────────────────────────────────
_RUTAS_PLANTILLA = [
    r"C:\Users\modulos6\OneDrive\AUTOCAD\PLANTILLA.dxf",
    r"S:\OneDrive\AUTOCAD\PLANTILLA.dxf",
    r"C:\Users\David\Desktop\AUTOCAD\PLANTILLA.dxf",
]
PLANTILLA_DXF  = next((r for r in _RUTAS_PLANTILLA if os.path.isfile(r)), _RUTAS_PLANTILLA[0])
CARPETA_SALIDA = os.path.join(os.path.dirname(PLANTILLA_DXF), "Generados")
TECNICO        = "D.P.Y."

# ─── ZONA DE LIMPIEZA (módulos de ejemplo en la plantilla) ────────────────────
ZONA_X = (340000.0, 490000.0)
ZONA_Y = (-132000.0, -95000.0)

# ─── DIMSTYLE POR DEFECTO ─────────────────────────────────────────────────────
DIMSTYLE = "PMP-T-50"

# ─── COLUMNAS CSV (separador ";", encoding utf-8-sig) ─────────────────────────
COL = {
    "fecha":0,"oferta":1,"numPedido":2,"cliente":3,"destino":4,
    "serie":5,"l":6,"a":7,"h":8,"estBase":9,"estCubierta":10,
    "estPilar":11,"panelGrosor":12,"panelTipo":13,"base":14,
    "acabado":15,"suministro":16,"perfilado":17,"colorPanel":18,
    "colorEstructura":19,"colorCarpinteria":20,"extra":21,
}

# ─── COLORES RAL ──────────────────────────────────────────────────────────────
MAPA_RAL = {
    "#4E5754":"RAL 7012","#3C3F3F":"RAL 7021","#C8C2B4":"RAL 7047",
    "#F5F5F5":"BCO. PANELAIS","#FFFFFF":"RAL 9010","#E8E0D5":"RAL 9001",
    "#1E213D":"RAL 5013","#6D7575":"RAL 7039",
}
MAPA_NOMBRE_RAL = {
    "9002": "BCO. PANELAIS",
}

# ─── OFFSETS CARRILES ─────────────────────────────────────────────────────────
# Medidos del módulo de referencia 6000x2350, panel 40mm
CARRIL_OFS_H_X      = 142   # offset X desde esquina → inicio carril horizontal
CARRIL_OFS_H_Y      = 40    # offset Y desde esquina → borde exterior carril horiz
CARRIL_OFS_V_X      = 40    # offset X desde esquina → borde exterior carril vert
CARRIL_OFS_V_Y_MAP  = {2350: 170, 2400: 195, 2440: 215}
CARRIL_OFS_H_X_MAP  = {1190: 90}   # override para módulo mini 1190 (pilar 125x125)
CARRIL_OFS_V_Y_MINI = 90            # offset V_Y módulo mini 1190
