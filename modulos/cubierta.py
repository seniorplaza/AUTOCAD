"""
cubierta.py — Generación del PLANO DE ESTRUCTURA (CUBIERTA).
"""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment

from .config      import COL
from .calculos    import calc_hcubierta, calc_correas, hex_a_ral
from .dxf_utils   import cota_h, cota_v, _attribs

# Diccionario de reglas de correas de cubierta (H PERFIL -> L_MODULO_MAX -> config_correas)
# La tabla usa L: 2300, 3000, 4000, 5000, 6000, 7000, 8000, >8000
# El valor es un array [cant_40, cant_50, cant_60, cant_75, cant_90]
# Para interpolación, buscaremos la primera llave >= L
TABLA_CUBIERTA = {
    129: {
        3000: [2, 1, 0, 0, 0], # 2x40, 1x50 (<=3000, covers 2300 & 3000)
        4000: [2, 3, 0, 0, 0],
        5000: [2, 3, 0, 0, 0],
        6000: [4, 3, 0, 0, 0],
        # >6000 -> None (not used)
    },
    160: {
        3000: [2, 1, 0, 0, 0],
        4000: [2, 3, 0, 0, 0],
        5000: [2, 3, 0, 0, 0],
        6000: [2, 2, 3, 0, 0],
        7000: [2, 2, 4, 0, 0],
        # >7000 -> None
    },
    190: {
        3000: [0, 2, 1, 0, 0], # 2x50, 1x60
        4000: [0, 2, 2, 1, 0], # 2x50, 2x60, 1x75
        5000: [0, 2, 2, 1, 0],
        6000: [0, 2, 2, 3, 0],
        7000: [0, 2, 2, 4, 0],
        99999: [0, 0, 4, 2, 3], # 8000+ -> 4x60, 2x75, 3x90
    }
}

def _get_correas_cubierta(L, hcubierta):
    h_key = 190
    if hcubierta <= 129: h_key = 129
    elif hcubierta <= 160: h_key = 160
    else: h_key = 190
    
    tabla_h = TABLA_CUBIERTA[h_key]
    keys = sorted(tabla_h.keys())
    for k in keys:
        if L <= k:
            return tabla_h[k]
    return tabla_h[keys[-1]]

def _distribuir_correas(config_correas):
    """
    Toma un array [c40, c50, c60, c75, c90] y devuelve una lista ordenada simétricamente
    de menor a mayor hacia el centro.
    Ej: [4, 3, 0, 0, 0] -> [40, 50, 40, 50, 40, 50, 40]
    Wait, la regla simétrica exacta para 3x50 y 4x40 es alternando.
    Vamos a hacerlo simple: menores a los lados, mayores al centro, alternando intercaladamente.
    """
    pool = []
    for val, count in zip([40, 50, 60, 75, 90], config_correas):
        pool.extend([val] * count)
    # Sort descending
    pool.sort(reverse=True)
    # Place symmetrically: biggest in middle, next alternating left/right
    res = [0] * len(pool)
    left = 0
    right = len(pool) - 1
    for i, val in enumerate(pool):
        if i % 2 == 0:
            res[(len(pool)//2) + (i//2) * (-1)**((i//2)%2)] = val # Complex alternating
            pass
    # A simpler symmetric approach:
    # We want [40, 50, 40, 50, 40, 50, 40] for [4, 3, 0, 0, 0].
    # Which is exactly sorted by [40, 40, 40, 40, 50, 50, 50] taking from edges? No.
    # We want [40, 40, 50, 50, 50, 40, 40] if we have 4x40 and 3x50.
    # To get this, we sort the pool and take the biggest ones for the middle.
    pool.sort() # [40, 40, 40, 40, 50, 50, 50]
    res2 = []
    while pool:
        if pool:
            res2.insert(0, pool.pop()) # Place biggest at middle (well, first is middle-ish)
        if pool:
            res2.append(pool.pop())
    return res2


def dibujar_estructura_cubierta(msp, doc, fila, MARCO_Y0):
    def c(cname):
        idx = COL.get(cname, -1)
        return fila[idx].strip() if 0 <= idx < len(fila) else ""

    L     = int(c("l")  or 6000)
    A     = int(c("a")  or 2350)
    base  = c("base")
    panel = c("panelGrosor")
    hcub  = calc_hcubierta(L, A, base, panel, c("cubierta"))
    
    col_est = hex_a_ral(c("colorEstructura"))
    fecha = c("fecha") or "10/06/2026"

    # Marco A3
    MARCO_X0 = 393890.0
    RATIO_A3 = 7110.0 / 5028.0
    
    OFS_COR_BOT = 321.0
    MARGEN_X = 400.0 # Ajuste final para minimizar el marco
    
    A3_W, A3_H  = 7110.0, 5028.0
    marco_w = max(float(L) + 2 * MARGEN_X, A3_W)
    marco_h = marco_w / RATIO_A3

    MARCO_X1 = MARCO_X0 + marco_w
    MARCO_Y1 = MARCO_Y0 + marco_h

    # Dibujar Cajetín A3 escalado
    sx = marco_w / A3_W
    sy = marco_h / A3_H

    if doc.blocks.get('CAJETIN_VALS'):
        ref_caj = msp.add_blockref('CAJETIN_VALS', insert=(MARCO_X0, MARCO_Y0), dxfattribs={
            'xscale': sx, 'yscale': sy, 'layer': '0'
        })
        # Rellenar atributos del cajetín
        _caj_vals = {
            'OB':         c("destino") or c("cliente") or "-",
            'RAL':        col_est or "-",
            'NS':         c("serie") or "-",
            'SUMINISTRO': c("suministro") or "ARMADO",
            'FECHA':      fecha,
            'OFERTA':     c("numPedido") or c("oferta") or "-",
        }
        _attribs(ref_caj, _caj_vals, doc)
    
    # Bloque NUMERO DE MODULOS (Arriba a la derecha) - Escala fjiada a 1.0
    blk_num_name = 'RECUADRO NÚMERO DE UD (MÓDULOS) NUMERO SERIE'
    if doc.blocks.get(blk_num_name):
        ref_num = msp.add_blockref(blk_num_name, insert=(MARCO_X1 - 1000*sx, MARCO_Y1 - 500*sy), dxfattribs={
            'xscale': 1.0, 'yscale': 1.0, 'layer': '0'
        })
        # Calcular unidades (Lógica de bloques.py)
        try:
            serie_val = c("serie")
            partes = (serie_val or '').replace(' ','').split('-')
            if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                n_uds = int(partes[1]) - int(partes[0]) + 1
            elif len(partes) >= 3:
                n_uds = len(partes)
            else:
                n_uds = 1
        except Exception:
            n_uds = 1
        uds_val = f"{n_uds} UNIDADES" if n_uds != 1 else "1 UNIDAD"
        _attribs(ref_num, {'4UNIDADES_1UNIDAD': uds_val}, doc)

    # Determinar configuración de correas
    config = _get_correas_cubierta(L, hcub)
    correas_list = _distribuir_correas(config)
    num_correas = len(correas_list)

    # 1. TÍTULO BLOCKREF
    cx = (MARCO_X0 + MARCO_X1) / 2.0
    cy_titulo = MARCO_Y0 + marco_h - 1535 # Bajado 535mm respecto a los 1000 originales
    
    msp.add_blockref('TÍTULO CUBIERTA', insert=(cx, cy_titulo), dxfattribs={'layer': 'TEXTO'})

    # Alturas de dibujo fijas para asegurar centrado y espaciado (subido 650mm total)
    cy_largo = MARCO_Y0 + marco_h - 2500
    cy_ancho = MARCO_Y0 + marco_h - 3350

    # 2. LARGO
    x_largo_ini = cx - L / 2.0
    x_largo_fin = cx + L / 2.0

    # Lineas grises del largo (4 líneas horizontales)
    for dy in [0, -37, -92, -129]:
        msp.add_line((x_largo_ini, cy_largo + dy), (x_largo_fin, cy_largo + dy), dxfattribs={'layer':'0', 'color':8})

    msp.add_blockref('PERFIL CARA CORTA CUBIERTA 129.40', insert=(x_largo_ini, cy_largo), dxfattribs={'layer':'0'})
    msp.add_blockref('PERFIL CARA CORTA CUBIERTA 129.40', insert=(x_largo_fin, cy_largo), dxfattribs={'layer':'0', 'xscale':-1})

    cota_h(msp, doc, x_largo_ini, cy_largo, x_largo_fin, cy_largo, cy_largo + 425, 'PMP-T-60')
    # Cota H en la derecha (más limpio y coherente con la sección de abajo)
    cota_v(msp, doc, x_largo_fin, cy_largo, x_largo_fin, cy_largo-hcub, x_largo_fin+150, 'PMP-T-50', color=5)

    # Posicionar correas (Distribución exacta L / N+1) sobre la 3ª línea (-92)
    esp_exacto = float(L) / (num_correas + 1)
    correa_x_pts = []
    cy_omega = cy_largo - 92
    for i, c_val in enumerate(correas_list):
        x_curr = x_largo_ini + esp_exacto * (i + 1)
        correa_x_pts.append(x_curr)
        # Dibujar bloque de correa OMEGA
        blk_name_omega = f"CORREA OMEGA {c_val}"
        if doc.blocks.get(blk_name_omega):
            msp.add_blockref(blk_name_omega, insert=(x_curr, cy_omega), dxfattribs={'layer':'0'})
        else:
            w = c_val
            msp.add_line((x_curr - w/2, cy_omega), (x_curr - w/2, cy_omega-hcub+92), dxfattribs={'layer':'0'})
            msp.add_line((x_curr + w/2, cy_omega), (x_curr + w/2, cy_omega-hcub+92), dxfattribs={'layer':'0'})
        
        # Identificador "OMEGA {valor}" y raya roja
        msp.add_mtext(f"OMEGA {c_val}", dxfattribs={
            'insert': (x_curr, cy_largo + 250), 'char_height': 50, 'attachment_point': 5, 'layer':'TEXTO', 'color': 2
        })
        msp.add_line((x_curr, cy_largo + 220), (x_curr, cy_largo), dxfattribs={'layer':'0', 'color':1})

    # Cotas abajo
    prev_x = x_largo_ini
    for px in correa_x_pts + [x_largo_fin]:
        cota_h(msp, doc, prev_x, cy_largo-hcub, px, cy_largo-hcub, cy_largo-hcub-200, 'PMP-T-50')
        prev_x = px

    # 3. ANCHO
    x_ancho_ini = cx - A / 2.0
    x_ancho_fin = cx + A / 2.0
    
    # (Removidas las líneas grises de cara larga por solicitud del usuario)

    msp.add_blockref('PERFIL CARA LARGA CUBIERTA 129.40', insert=(x_ancho_ini, cy_ancho), dxfattribs={'layer':'0'})
    msp.add_blockref('PERFIL CARA LARGA CUBIERTA 129.40', insert=(x_ancho_fin, cy_ancho), dxfattribs={'layer':'0', 'xscale':-1})
    msp.add_blockref('PERFIL INTERNO CL', insert=(x_ancho_ini+36, cy_ancho-127), dxfattribs={'layer':'0'})
    msp.add_blockref('PERFIL INTERNO CL', insert=(x_ancho_fin-36, cy_ancho-127), dxfattribs={'layer':'0', 'xscale': -1})
    
    # Falso techo (lamas)
    msp.add_lwpolyline([(x_ancho_ini+82, cy_ancho-107), (x_ancho_fin-82, cy_ancho-107), 
                        (x_ancho_fin-82, cy_ancho-127), (x_ancho_ini+82, cy_ancho-127)], 
                       close=True, dxfattribs={'layer': 'Lama Falso techo', 'color': 256})
    
    # Chapa Trape Centrada (Bloque insertado desde el borde izquierdo)
    num_chapas = 2 if A <= 2500 else 3
    cx_chapas = x_ancho_ini + A/2
    start_chapa = cx_chapas - (num_chapas * 800) / 2
    for i in range(num_chapas):
        msp.add_blockref('CHAPA TRAPE 6G', insert=(start_chapa + i*800, cy_ancho-9), dxfattribs={'layer':'0'})

    # Lineas grises correa
    max_correa = max(correas_list) if correas_list else 50
    msp.add_line((x_ancho_ini+36, cy_ancho-37), (x_ancho_fin-36, cy_ancho-37), dxfattribs={'layer': 'Estructura C F'})
    msp.add_line((x_ancho_ini+36, cy_ancho-37-max_correa), (x_ancho_fin-36, cy_ancho-37-max_correa), dxfattribs={'layer': 'Estructura C F'})

    # Cota horizontal subida 85mm: 450 - 85 = 365
    cota_h(msp, doc, x_ancho_ini, cy_ancho, x_ancho_fin, cy_ancho, cy_ancho-hcub-365, 'PMP-T-60')
    # Cota vertical H invertida y más pequeña
    cota_v(msp, doc, x_ancho_fin, cy_ancho, x_ancho_fin, cy_ancho-hcub, x_ancho_fin+150, 'PMP-T-50', color=5)

    # CALLOUTS / LEYENDAS (USANDO BLOQUES)
    msp.add_blockref('VIERTE AGUAS', insert=(x_ancho_ini+40, cy_ancho-10), dxfattribs={'layer': 'TEXTO'})
    # Subir 240, derecha 210
    msp.add_blockref('CHAPA TRAPE 6G TEXTO', insert=(cx_chapas+210, cy_ancho+245), dxfattribs={'layer': 'TEXTO'})
    msp.add_blockref('CORREA OMEGA', insert=(x_ancho_fin-100, cy_ancho-50), dxfattribs={'layer': 'TEXTO'})
    # Izquierda 650 (200+650=850)
    msp.add_blockref('FALSO TECHO', insert=(cx_chapas-850, cy_ancho-115), dxfattribs={'layer': 'TEXTO'})
    # Derecha 230 (200+230=430)
    msp.add_blockref('AISLAMIENTO', insert=(cx_chapas+430, cy_ancho-70), dxfattribs={'layer': 'TEXTO'})

    # Leyenda Correas Izquierda
    leyenda_x = x_ancho_ini - 600
    leyenda_y = cy_ancho - 50
    msp.add_mtext("CORREAS", dxfattribs={
        'insert': (leyenda_x, leyenda_y + 100), 'char_height': 75, 'attachment_point': 5, 'layer': 'TEXTO', 'color': 2
    })
    
    unique_types = sorted(list(set(correas_list)))
    blk_name = "BLOQUE CORREAS " + ".".join(str(v) for v in unique_types)
    if not doc.blocks.get(blk_name):
        blk_name = "BLOQUE CORREAS 40.50" # default
    msp.add_blockref(blk_name, insert=(leyenda_x, leyenda_y), dxfattribs={'layer': '0', 'xscale': 2, 'yscale': 2})
    
    return marco_h
