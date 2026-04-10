"""
config.py — Constantes globales del proyecto de generación de planos DXF.
Rutas, columnas CSV, capas, colores, offsets de carriles y zonas de limpieza.
"""
import os

# ─── RUTAS ────────────────────────────────────────────────────────────────────
_RUTAS_PLANTILLA = [
    r"C:\Users\modulos6\OneDrive\AUTOCAD-1\PLANTILLA.dxf",
    r"S:\OneDrive\AUTOCAD-1\PLANTILLA.dxf",
    r"C:\Users\David\Desktop\AUTOCAD-1\PLANTILLA.dxf",
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
    "estPilar":11,"cubierta":12,"panelGrosor":13,"panelTipo":14,
    "base":15,"acabado":16,"suministro":17,"perfilado":18,
    "colorPanel":19,"colorEstructura":20,"colorCarpinteria":21,"extra":22,
    # cols 23-33 son metadata del gestor (folderPath, impreso, etc.)
    "modulo":34,"cantidad":35,"conjunto":36,"adosamiento":37,"conjuntoVinculado":38,
}

# ─── COLORES RAL ──────────────────────────────────────────────────────────────
MAPA_RAL = {
    "#F5F5F5":"BCO. PANELAIS",
    "#BEBD7F":"RAL 1000","#C2B078":"RAL 1001","#C6A664":"RAL 1002",
    "#E5BE01":"RAL 1003","#CDA434":"RAL 1004","#A98307":"RAL 1005",
    "#E4A010":"RAL 1006","#DC9D00":"RAL 1007",
    "#ED760E":"RAL 2000","#C93C20":"RAL 2001","#CB2821":"RAL 2002",
    "#FF7514":"RAL 2003","#F44611":"RAL 2004",
    "#AF2B1E":"RAL 3000","#A52019":"RAL 3001","#A2231D":"RAL 3002",
    "#9B111E":"RAL 3003","#75151E":"RAL 3004","#5E2129":"RAL 3005",
    "#6D3F5B":"RAL 4001","#922B3E":"RAL 4002","#DE4C8A":"RAL 4003","#641C34":"RAL 4004",
    "#354D73":"RAL 5000","#1F3438":"RAL 5001","#20214F":"RAL 5002",
    "#1D1E33":"RAL 5003","#18171C":"RAL 5004","#1E2460":"RAL 5005",
    "#3E5F8A":"RAL 5007","#26252D":"RAL 5008","#025669":"RAL 5009",
    "#0E4C8A":"RAL 5010","#231A24":"RAL 5011","#3B83BD":"RAL 5012",
    "#1E213D":"RAL 5013","#606E8C":"RAL 5014","#2271B3":"RAL 5015",
    "#316650":"RAL 6000","#287233":"RAL 6001","#2D572C":"RAL 6002",
    "#424632":"RAL 6003","#1F3A3D":"RAL 6004","#2F4538":"RAL 6005",
    "#3E3B32":"RAL 6006","#343B29":"RAL 6007","#39352A":"RAL 6008",
    "#31372B":"RAL 6009","#35682D":"RAL 6010","#587246":"RAL 6011",
    "#343E40":"RAL 6012","#6C7156":"RAL 6013","#47402E":"RAL 6014",
    "#3B3C36":"RAL 6015","#1E5945":"RAL 6016","#4C9141":"RAL 6017",
    "#57A639":"RAL 6018","#BDECB6":"RAL 6019","#2E3A23":"RAL 6020",
    "#89AC76":"RAL 6021","#308446":"RAL 6024","#3D642D":"RAL 6025",
    "#015D52":"RAL 6026","#84C3BE":"RAL 6027","#2C5545":"RAL 6028",
    "#20603D":"RAL 6029","#317F43":"RAL 6032","#497E76":"RAL 6033","#7FB5B5":"RAL 6034",
    "#78858B":"RAL 7000","#8A9597":"RAL 7001","#7E7B52":"RAL 7002",
    "#6C7059":"RAL 7003","#969992":"RAL 7004","#646B63":"RAL 7005",
    "#6D6552":"RAL 7006","#6A5F31":"RAL 7008","#4D5645":"RAL 7009",
    "#4C514A":"RAL 7010","#434B4D":"RAL 7011","#4E5754":"RAL 7012",
    "#464531":"RAL 7013","#434750":"RAL 7015","#293133":"RAL 7016",
    "#23282B":"RAL 7021","#332F2C":"RAL 7022","#686C5E":"RAL 7023",
    "#474A51":"RAL 7024","#2F353B":"RAL 7026","#8B8C7A":"RAL 7030",
    "#474B4E":"RAL 7031","#B8B799":"RAL 7032","#7D8471":"RAL 7033",
    "#8F8B66":"RAL 7034","#D7D7D7":"RAL 7035","#7F7679":"RAL 7036",
    "#7D7F7D":"RAL 7037","#B5B8B1":"RAL 7038","#6C6960":"RAL 7039",
    "#9DA1AA":"RAL 7040","#8D948D":"RAL 7042","#4E5452":"RAL 7043","#CAC4B0":"RAL 7044",
    "#826C34":"RAL 8000","#955F20":"RAL 8001","#6C3B2A":"RAL 8002",
    "#734222":"RAL 8003","#8E402A":"RAL 8004","#59351F":"RAL 8007",
    "#6F4F28":"RAL 8008","#5B3A29":"RAL 8011","#592321":"RAL 8012",
    "#382C1E":"RAL 8014","#633A34":"RAL 8015","#4C2F27":"RAL 8016",
    "#45322E":"RAL 8017","#403A3A":"RAL 8019","#212121":"RAL 8022",
    "#A65E2E":"RAL 8023","#79553D":"RAL 8024","#755C48":"RAL 8025","#4E3B31":"RAL 8028",
    "#FDF4E3":"RAL 9001","#E7EBDA":"RAL 9002","#F4F4F4":"RAL 9003",
    "#282828":"RAL 9004","#0A0A0A":"RAL 9005","#A5A5A5":"RAL 9006",
    "#8F8F8F":"RAL 9007","#FFFFFF":"RAL 9010","#1C1C1C":"RAL 9011",
    "#F6F6F6":"RAL 9016","#1E1E1E":"RAL 9017",
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
