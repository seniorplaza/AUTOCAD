"""
calculos.py — Funciones de cálculo de dimensiones del módulo.
calc_hbase, calc_hcubierta, calc_correas, grosor_carril, nombre_bloque_pilar, hex_a_ral.
"""
from .config import MAPA_RAL, MAPA_NOMBRE_RAL, CARRIL_OFS_V_X


def hex_a_ral(v):
    if not v: return ""
    v = v.strip()
    if "RAL" in v.upper():
        partes = v.upper().split("RAL")
        if len(partes) > 1:
            cod   = partes[1].strip().split()[0].split("-")[0]
            mate  = "MATE" if "MATE" in v.upper() else ""
            ral_str = f"RAL {cod} {mate}".strip()
            return MAPA_NOMBRE_RAL.get(cod, ral_str)
        return v
    return MAPA_RAL.get(v.upper(), "")


def calc_hbase(l, a, base, panel):
    """
    Altura del perfil de base según tipo y dimensiones.
    HORMIGONADA devuelve string "UPN Xmm". Resto devuelve entero (mm).
    NOTA: panel exactamente 50mm usa carril e50 → NO sube a 160 (condición p > 50).
    """
    try: L=int(l); A=int(a); p=int(panel) if panel else 0
    except: return 137
    t = (base or "").strip().upper()
    if t == "HORMIGONADA": return "UPN 140" if L <= 7000 else "UPN 160"
    if t == "TRAMEX":      return 200
    if t == "SANEAMIENTO": return 240
    v = 137 if L <= 6000 else 160 if L <= 8500 else 200
    if p > 50: v = max(v, 160)
    if A > 2500: v = max(v, 160)
    return v


def calc_hcubierta(l, a, base, panel, cubierta):
    try: L=int(l); A=int(a); p=int(panel) if panel else 0
    except: return 129
    tb = (base    or "").strip().upper()
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


def grosor_carril(panel_grosor):
    """Grosor del carril en mm según el grosor del panel (mín 40mm)."""
    try:
        p = int(panel_grosor)
        if   p <= 40: return 40
        elif p <= 50: return 50
        elif p <= 70: return 60
        elif p <= 90: return 80
        else:         return 100
    except (ValueError, TypeError):
        return 40


def calc_correas(L, base_str, A=None, g_carril=40):
    """
    Posiciones X (relativas a x0) de cada correa y paso de tablero.
    Regla última correa: siempre al punto medio de la última cota de tablero.
    """
    if A is not None and int(A) <= 1190:
        return [round(int(L) / 2)], 1220
    t = (base_str or "").strip().upper()
    t = t.replace("Ó","O").replace("É","E").replace("Í","I")
    inicio, paso, tablero = (710,625,1250) if "FENOL" in t else (695,610,1220)
    posiciones, x = [], inicio
    while x <= L - 5:
        posiciones.append(round(x))
        x += paso
    # Última correa: midpoint de la última cota de tablero,
    # SALVO que esa cota sea muy estrecha (< tablero/2) → se queda en su inicio
    x_ini = CARRIL_OFS_V_X + g_carril + 5
    x_fin = L - CARRIL_OFS_V_X - g_carril - 5
    xt = x_ini
    while xt + tablero < x_fin:
        xt += tablero
    last_cota_w = x_fin - xt
    if last_cota_w >= tablero / 2:
        last_pos = round((xt + x_fin) / 2)   # cota ancha → midpoint
    else:
        last_pos = round(xt)                  # cota estrecha → inicio de la cota
    if posiciones:
        posiciones[-1] = last_pos
    return posiciones, tablero
